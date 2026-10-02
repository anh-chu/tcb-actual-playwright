import asyncio
import json
import logging
import datetime
import os
import time
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright
from modules import convert, actual
from modules.logger import logger

TCB_DASHBOARD_URL = "https://onlinebanking.techcombank.com.vn/dashboard"
TCB_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"

# The browser runs with a persistent Chromium profile stored inside the data/
# volume (same convention as the database). Cookies survive between runs, so a run
# that lands while TCB's cookies are still valid skips the cold login, which is
# what triggers the phone approval. TCB's cookies are short-lived (minutes), so
# this mostly saves a second approval right after a failed run; the fallback is
# the normal credential login. Override with TCB_BROWSER_PROFILE if needed.
BROWSER_PROFILE_DIR = os.environ.get(
    "TCB_BROWSER_PROFILE",
    str(Path(__file__).resolve().parent / "data" / "browser_profile"),
)
# Chromium refuses to launch on a profile whose singleton lock looks held; a run
# that was killed (redeploy, container restart, OOM) leaves these behind.
_BROWSER_SINGLETON_FILES = ("SingletonLock", "SingletonSocket", "SingletonCookie")
# storageState dump: captures ALL cookies including session cookies, which Chromium
# itself drops when the browser closes. Written after every run, re-injected before
# the next navigation so a still-valid TCB session survives between runs.
BROWSER_STATE_FILE = str(Path(BROWSER_PROFILE_DIR).parent / "browser_state.json")

class AppStatus(str, Enum):
    IDLE = "idle"
    STARTING = "starting"
    LOGGING_IN = "logging_in"
    WAITING_OTP = "waiting_otp"
    FETCHING_DATA = "fetching_data"
    SAVING_DATA = "saving_data"
    SUCCESS = "success"
    ERROR = "error"

from collections import deque

class ListHandler(logging.Handler):
    def __init__(self, log_list, max_len=100):
        super().__init__()
        self.log_list = log_list
        self.max_len = max_len
        self.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))

    def emit(self, record):
        msg = self.format(record)
        self.log_list.append(msg)
        if len(self.log_list) > self.max_len:
             self.log_list.popleft()

class BankingService:
    def __init__(self):
        self._status = AppStatus.IDLE
        self._last_error = ""
        self._running = False
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._latest_screenshot: Optional[bytes] = None
        self._logs = deque(maxlen=50)
        self._last_result: Optional[dict] = None
        
        # Attach handler
        self._log_handler = ListHandler(self._logs)
        logger.addHandler(self._log_handler)
        
    @property
    def logs(self) -> list[str]:
        return list(self._logs)
        
    @property
    def status(self) -> AppStatus:
        return self._status

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def last_result(self) -> Optional[dict]:
        return self._last_result

    def get_latest_screenshot(self) -> Optional[bytes]:
        return self._latest_screenshot

    async def start_sync(self, config: dict):
        if self._running:
            raise Exception("Sync already in progress")
        self._running = True
        self._config = config
        # A stale error from the previous run would otherwise sit on the dashboard
        # forever, even after a later sync succeeds.
        self._last_error = ""
        self._last_result = None
        # Store the task so we can cancel it
        self._sync_task = asyncio.create_task(self._run_process())

    async def stop_sync(self):
        logger.info("Stop requested by user")
        self._running = False
        # Cancel the sync task if it exists
        if hasattr(self, '_sync_task') and self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                logger.info("Sync task cancelled successfully")
        self._set_status(AppStatus.IDLE)

    def _set_status(self, status: AppStatus):
        self._status = status
        logger.info(f"Status changed to: {status}")

    def _prepare_browser_profile(self):
        profile = Path(BROWSER_PROFILE_DIR)
        profile.mkdir(parents=True, exist_ok=True)
        # A run that was killed (redeploy, container restart, OOM) leaves Chromium's
        # singleton files behind; a stale lock makes the next launch refuse to start.
        for name in _BROWSER_SINGLETON_FILES:
            try:
                (profile / name).unlink()
            except FileNotFoundError:
                pass
        logger.info(f"Using browser profile at {BROWSER_PROFILE_DIR}")

    async def _restore_cookies_from_state(self):
        """Re-inject the cookies saved by the previous run.

        Chromium's profile keeps only non-session cookies; key session cookies
        (Keycloak SSO) are dropped when the browser closes. storageState() captured
        them anyway, so put them back before the first navigation. Stale cookies
        are ignored naturally: the session probe detects the sign-in form then.
        """
        state_file = Path(BROWSER_STATE_FILE)
        if not state_file.is_file():
            return
        try:
            state = json.loads(state_file.read_text())
        except Exception as e:
            logger.warning(f"Could not read the stored cookie state: {e}")
            return
        added = 0
        for cookie in state.get("cookies") or []:
            try:
                await self._context.add_cookies([cookie])
                added += 1
            except Exception:
                pass  # skip anything malformed rather than lose the whole batch
        if added:
            logger.info(f"Restored {added} saved cookie(s) from the previous run")

    async def _save_cookies_state(self):
        """Persist the whole cookie jar, including session cookies Chromium drops."""
        state = await self._context.storage_state()
        path = Path(BROWSER_STATE_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state))
        os.chmod(tmp, 0o600)
        tmp.replace(path)

    async def _run_process(self):
        screenshot_task = None
        try:
            self._set_status(AppStatus.STARTING)
            async with async_playwright() as self._playwright:
                try:
                    self._prepare_browser_profile()
                    self._context = await self._playwright.chromium.launch_persistent_context(
                        BROWSER_PROFILE_DIR,
                        headless=True,
                        viewport={"width": 1920, "height": 1080},
                        user_agent=TCB_USER_AGENT,
                        args=[
                            "--no-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-gpu",
                            "--window-size=1920,1080",
                        ],
                    )
                    # A persistent context owns the whole browser process; closing the
                    # context below is enough, self._browser stays None.
                    self._browser = None
                    self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()

                    # Put back the cookies saved by the previous run (including the
                    # session cookies Chromium itself would have dropped).
                    await self._restore_cookies_from_state()

                    # Start background screenshot task
                    screenshot_task = asyncio.create_task(self._screenshot_loop())

                    if self._running:
                        await self._process_login()

                    if self._running:
                        await self._process_fetch()
                finally:
                    # Persist the cookie jar, then close the browser while playwright
                    # is still running so the profile is flushed to disk cleanly.
                    if self._context:
                        try:
                            await asyncio.wait_for(self._save_cookies_state(), timeout=5)
                        except Exception:
                            pass
                        try:
                            await asyncio.wait_for(self._context.close(), timeout=10)
                        except Exception:
                            pass
                    self._context = None
                    self._page = None
                    self._browser = None

        except asyncio.CancelledError:
            logger.info("Sync process cancelled")
            self._set_status(AppStatus.IDLE)
            raise
        except Exception as e:
            err_msg = str(e)
            # Suppress noisy Playwright errors during manual stop
            cancellation_keywords = ["net::ERR_ABORTED", "Page closed", "Target closed", "browser has been closed"]
            is_cancellation_error = any(k in err_msg for k in cancellation_keywords)
            
            if not self._running or is_cancellation_error:
                logger.info(f"Sync stopped or cancelled: {err_msg}")
                if self._status != AppStatus.SUCCESS:
                    self._set_status(AppStatus.IDLE)
            else:
                logger.error(f"Error during sync: {err_msg}")
                self._last_error = err_msg
                self._set_status(AppStatus.ERROR)
        finally:
            self._running = False
            if screenshot_task:
                screenshot_task.cancel()
                try:
                    await screenshot_task
                except asyncio.CancelledError:
                    pass

            if self._status != AppStatus.ERROR and self._status != AppStatus.SUCCESS:
                 self._set_status(AppStatus.IDLE)


    async def _screenshot_loop(self):
        while self._running:
            if self._page and not self._page.is_closed():
                try:
                    self._latest_screenshot = await self._page.screenshot(type="jpeg", quality=50)
                except Exception:
                    pass
            await asyncio.sleep(0.5)

    async def _process_login(self):
        self._set_status(AppStatus.LOGGING_IN)
        logger.info("Navigating to dashboard...")
        await self._page.goto(TCB_DASHBOARD_URL)

        if await self._resume_session_if_valid():
            logger.info("Existing TCB session reused from the browser profile")
        else:
            await self._login_with_credentials()

        self._set_status(AppStatus.FETCHING_DATA)
        logger.info("Logged in successfully!")

    async def _resume_session_if_valid(self) -> bool:
        """Return True when the persisted profile still yields an authenticated session.

        After /dashboard loads, the app either bounces to the Keycloak sign-in form
        (stored cookies no longer work: cold) or silently (re)mints an OIDC session
        from the stored Keycloak cookies (warm). Whichever signal settles first
        decides; a stale sessionStorage token from an earlier run does not count.
        """
        probe = """() => {
            if (document.querySelector('#username')) return 'cold';
            try {
                const token = sessionStorage.getItem('access_token');
                if (token) {
                    let exp = sessionStorage.getItem('expires_at');
                    exp = exp === null ? null : Number(exp);
                    if (exp !== null && !isNaN(exp) && exp < 1e11) exp = exp * 1000;  // seconds -> ms
                    const fresh = exp === null || isNaN(exp) ? true : exp > Date.now();
                    if (fresh) return 'warm';
                }
            } catch (e) {}
            return '';
        }"""
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            try:
                verdict = await self._page.evaluate(probe)
            except Exception:
                verdict = ""  # navigation in flight; re-check on the next pass
            if verdict == "cold":
                logger.info("Keycloak sign-in form detected; stored cookies are no longer valid")
                return False
            if verdict == "warm":
                logger.info("Stored cookies still mint a session; skipping login")
                return True
            await asyncio.sleep(0.5)
        logger.info("No existing session could be confirmed; falling back to a full login")
        return False

    async def _login_with_credentials(self):
        try:
            await self._page.locator("#username").wait_for(state="visible", timeout=15000)
        except Exception:
            raise Exception(
                "No reusable session, and the sign-in form never appeared; cannot log in"
            )

        logger.info("Signing in with the stored credentials")
        await self._page.locator("#username").fill(self._config["tcb_username"])
        await self._page.locator("#password").click()
        await self._page.locator("#password").fill(self._config["tcb_password"])
        await self._page.locator("#kc-login").click()

        # TCB pushes an approval request to the registered phone; it expires
        # server-side in about 2 minutes. Surface the waiting_otp status for the
        # long wait, like before.
        logger.info("Waiting for login completion (phone approval may be required)")
        outcome = await self._wait_for_login_outcome(5000)
        if outcome is None:
            self._set_status(AppStatus.WAITING_OTP)
            outcome = await self._wait_for_login_outcome(120000)
        if outcome is None:
            raise Exception(
                "Timed out waiting for the login to complete (phone approval not done in time?)"
            )
        if outcome != "ok":
            raise Exception(f"Keycloak rejected the login: {outcome}")

    async def _wait_for_login_outcome(self, timeout_ms: int) -> Optional[str]:
        """Watch the post-login page.

        Returns 'ok' once the SPA holds a live token, the error text when Keycloak
        shows a visible error, or None when nothing settled within the timeout.
        """
        probe = """() => {
            if (location.pathname.indexOf('/auth/realms') === -1) {
                try {
                    const token = sessionStorage.getItem('access_token');
                    if (token) {
                        let exp = sessionStorage.getItem('expires_at');
                        exp = exp === null ? null : Number(exp);
                        if (exp !== null && !isNaN(exp) && exp < 1e11) exp = exp * 1000;  // seconds -> ms
                        const fresh = exp === null || isNaN(exp) ? true : exp > Date.now();
                        if (fresh) return 'ok';
                    }
                } catch (e) {}
                if (document.querySelector('.user-context-menu-info__container__name')) return 'ok';
            }
            const err = document.querySelector('#kc-error-message, #input-error');
            if (err && err.offsetParent !== null) {
                const text = (err.textContent || '').trim().replace(/\\s+/g, ' ');
                if (text) return 'error: ' + text.slice(0, 300);
            }
            return '';
        }"""
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            try:
                verdict = await self._page.evaluate(probe)
            except Exception:
                verdict = ""
            if verdict == "ok":
                return verdict
            if verdict.startswith("error:"):
                return verdict[len("error:"):].strip()
            await asyncio.sleep(0.75)
        return None

    async def _resolve_bearer_token(self) -> Optional[str]:
        """Resolve a bearer token for the TCB APIs.

        Prefer the SPA's sessionStorage token: it is minted (or refreshed) on every
        boot, so it is the freshest value on a reused session. Fall back to the
        Authorization cookie, which is the path this app has always used.
        """
        probe = "() => { try { return sessionStorage.getItem('access_token') || ''; } catch (e) { return ''; } }"
        spa_deadline = time.monotonic() + 3.0
        hard_deadline = time.monotonic() + 15.0
        cookie_token = None
        while time.monotonic() < hard_deadline:
            try:
                token = await self._page.evaluate(probe)
            except Exception:
                token = ""
            if token:
                return token
            cookie_token = await self._authorization_cookie()
            if cookie_token and time.monotonic() >= spa_deadline:
                return cookie_token
            await asyncio.sleep(0.5)
        return cookie_token

    async def _authorization_cookie(self) -> Optional[str]:
        for cookie in await self._context.cookies():
            if cookie["name"] == "Authorization" and cookie["domain"] == "onlinebanking.techcombank.com.vn":
                return cookie["value"]
        return None

    async def _process_fetch(self):
        self._set_status(AppStatus.FETCHING_DATA)
        logger.info("Fetching data...")
        
        try:
            token = await self._resolve_bearer_token()
            if not token:
                raise Exception(
                    "No usable TCB token found (neither the SPA session token nor the Authorization cookie)"
                )

            logger.info("Found authorization token")

            headers = {
                "User-Agent": TCB_USER_AGENT,
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.7,vi;q=0.3",
                "Referer": "https://onlinebanking.techcombank.com.vn/",
                "Authorization": f"Bearer {token}",
            }

            # Refresh transaction history on TCB side before reading.
            # Without this, the listing endpoint can return stale data.
            arrangement_ids = list(self._config.get("accounts_mapping", {}).keys())
            if arrangement_ids:
                refresh_url = "https://onlinebanking.techcombank.com.vn/api/sync-dis/client-api/v1/transactions/refresh"
                logger.info(f"Refreshing transactions for {len(arrangement_ids)} arrangement(s)")
                refresh_resp = await self._page.request.post(
                    url=refresh_url,
                    headers={**headers, "Content-Type": "application/json"},
                    data=json.dumps({"externalArrangementIds": arrangement_ids}),
                )
                if refresh_resp.status >= 400:
                    logger.warning(f"Refresh returned status {refresh_resp.status}, continuing anyway")
                else:
                    logger.info("Refresh accepted")
            else:
                logger.warning("No arrangement IDs in mapping, skipping refresh")

            # Calculate date range
            
            # Use custom dates if provided, otherwise default to last 30 days
            if self._config.get("date_from") and self._config.get("date_to"):
                date_from = self._config["date_from"]
                date_to = self._config["date_to"]
                logger.info(f"Using custom date range: {date_from} to {date_to}")
            else:
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                month_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
                date_from = month_ago
                date_to = today
                logger.info(f"Using default date range (last 30 days): {date_from} to {date_to}")
            
            # Make API call to get transactions
            url = f"https://onlinebanking.techcombank.com.vn/api/transaction-manager/client-api/v2/transactions?bookingDateGreaterThan={date_from}&bookingDateLessThan={date_to}&from=0&size=500&orderBy=bookingDate&direction=DESC"

            response = await self._page.request.get(url=url, headers=headers)
            
            if response.status != 200:
                raise Exception(f"API returned status {response.status}")
            
            body = await response.text()
            logger.info(f"Got {len(body)} bytes of transaction data from {date_from} to {date_to}")
            
            await self._process_save(body)

        except Exception as e:
            logger.error(f"Fetch flow failed: {e}")
            self._last_error = str(e)
            self._set_status(AppStatus.ERROR)
            raise

    async def _process_save(self, data_str: str):
         self._set_status(AppStatus.SAVING_DATA)
         data_json = json.loads(data_str)
         
         logger.info(f"Data type: {type(data_json)}")
         transactions_list = []

         logger.debug(f"Data keys: {list(data_json.keys()) if isinstance(data_json, dict) else 'N/A'}")
         
         if isinstance(data_json, list):
             # Direct list of transactions (from the proper API)
             transactions_list = data_json
         elif isinstance(data_json, dict):
             # Nested structure - try various paths
             if "document" in data_json and isinstance(data_json["document"], dict):
                 if "listTransaction" in data_json["document"]:
                     transactions_list = data_json["document"]["listTransaction"]
             elif "transactions" in data_json:
                 transactions_list = data_json["transactions"]
             elif "value" in data_json and isinstance(data_json["value"], list):
                 transactions_list = data_json["value"]
             elif "data" in data_json and isinstance(data_json["data"], list):
                 transactions_list = data_json["data"]
         
         if not transactions_list:
              logger.warning("Could not find a list of transactions in the response!")
              # We might continue to extract empty, or fail. 
              # For now, let's pass what we have if it's a list, otherwise empty.
              if not isinstance(transactions_list, list):
                  transactions_list = []

         logger.info(f"Converting {len(transactions_list)} transactions...")
         
         mapping = self._config.get("accounts_mapping", {})
         orphaned = convert.unmapped_arrangements(transactions_list, mapping)
         if orphaned:
             detail = ", ".join(f"{a} ({n} txns)" for a, n in orphaned.items())
             logger.warning(f"Skipped {sum(orphaned.values())} transaction(s) from unmapped arrangement(s): {detail}")

         converted = convert.convert_to_transactions(transactions_list, mapping)

         if not converted:
             logger.warning("Nothing to import: no transactions matched the account mapping")
             self._set_status(AppStatus.SUCCESS)
             return

         logger.info("Fetching Actual's token...")
         loop = asyncio.get_event_loop()

         actual_config = {
             "url": self._config["actual_url"],
             "password": self._config["actual_password"],
             "budget_id": self._config["actual_budget_id"],
             "budget_password": self._config.get("actual_budget_password")
         }

         actual_token = await loop.run_in_executor(None, lambda: actual.init_actual(actual_config))

         summary = {
             "date_from": self._config.get("date_from"),
             "date_to": self._config.get("date_to"),
             "transactions_fetched": len(transactions_list),
             "skipped_unmapped": sum(orphaned.values()),
             "unmapped_arrangements": orphaned,
             "accounts": {},
             "total_added": 0,
             "total_updated": 0,
         }

         logger.info(f"Importing data to Actual for {len(converted)} account(s)...")
         # partial() binds the loop variables by value. A bare lambda captures them
         # by reference and can import every account's transactions into whichever
         # account the loop happened to finish on.
         for account, transactions in converted.items():
             result = await loop.run_in_executor(
                 None,
                 partial(
                     actual.import_transactions,
                     actual_token,
                     account,
                     transactions,
                     actual_config["url"],
                 ),
             )
             added = len(result.get("added", [])) if isinstance(result, dict) else 0
             updated = len(result.get("updated", [])) if isinstance(result, dict) else 0
             summary["accounts"][account] = {
                 "sent": len(transactions),
                 "added": added,
                 "updated": updated,
             }
             summary["total_added"] += added
             summary["total_updated"] += updated
             logger.info(
                 f"  account {account}: {len(transactions)} sent, {added} added, {updated} updated"
             )

         summary["finished_at"] = datetime.datetime.now().isoformat(timespec="seconds")
         self._last_result = summary
         logger.info(
             f"Done: {summary['total_added']} added, {summary['total_updated']} updated"
        )
         self._set_status(AppStatus.SUCCESS)

banking_service = BankingService()
