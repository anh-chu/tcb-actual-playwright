import asyncio
import json
import logging
import datetime
from enum import Enum
from typing import Optional
from playwright.async_api import async_playwright, Playwright, Page, Browser, BrowserContext, expect
from modules import convert, actual
from modules.logger import logger

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

    def get_latest_screenshot(self) -> Optional[bytes]:
        return self._latest_screenshot

    async def start_sync(self, config: dict):
        if self._running:
            raise Exception("Sync already in progress")
        self._running = True
        self._config = config
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

    async def _run_process(self):
        screenshot_task = None
        try:
            self._set_status(AppStatus.STARTING)
            async with async_playwright() as self._playwright:
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--window-size=1920,1080",
                    ],
                )
                
                self._context = await self._browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
                )
                
                self._page = await self._context.new_page()
                
                # Start background screenshot task
                screenshot_task = asyncio.create_task(self._screenshot_loop())

                if self._running:
                    await self._process_login()
                
                if self._running:
                    await self._process_fetch()

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
                
            if self._context:
                try: await self._context.close()
                except: pass
            if self._browser:
                try: await self._browser.close()
                except: pass
            
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
        await self._page.goto("https://onlinebanking.techcombank.com.vn/dashboard")
        
        await expect(self._page.locator("#username")).to_be_visible()
        await self._page.locator("#username").fill(self._config["tcb_username"])
        await self._page.locator("#password").click()
        await self._page.locator("#password").fill(self._config["tcb_password"])
        await self._page.locator("#kc-login").click()

        logger.info("Waiting for login completion (OTP or dashboard load)")
        
        # We try to wait for successful login
        try:
             # Wait short time (5s)
             await expect(self._page.locator(".user-context-menu-info__container__name")).to_be_attached(timeout=5000)
        except:
             # If timed out, we likely need OTP
             self._set_status(AppStatus.WAITING_OTP)
             # Wait longer (2 mins)
             await expect(self._page.locator(".user-context-menu-info__container__name")).to_be_attached(timeout=120000)

        self._set_status(AppStatus.LOGGING_IN)
        logger.info("Logged in successfully!")
    async def _process_fetch(self):
        self._set_status(AppStatus.FETCHING_DATA)
        logger.info("Fetching data...")
        
        try:
            # Extract Authorization token from cookies
            cookies = await self._context.cookies()
            auth_cookie = None
            for cookie in cookies:
                if cookie['name'] == 'Authorization' and cookie['domain'] == 'onlinebanking.techcombank.com.vn':
                    auth_cookie = cookie['value']
                    break
            
            if not auth_cookie:
                raise Exception("Could not find Authorization cookie")
            
            logger.info("Found authorization token")
            
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
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.7,vi;q=0.3",
                "Referer": "https://onlinebanking.techcombank.com.vn/",
                "Authorization": f"Bearer {auth_cookie}",
            }
            
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
            raise e

        except Exception as e:
            logger.error(f"Fetch flow failed: {e}")
            self._last_error = str(e)
            self._set_status(AppStatus.ERROR)
            raise e

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
         
         # Make sure convert module uses the mapping passed in config
         # We need to temporarily patch or pass mapping to convert function
         # For now, let's assume convert module is modified or we do it here.
         # Actually, better to modify convert module to accept mapping.
         # But for speed, let's modify convert module in a separate step or monkeypatch for now?
         # No, cleaner to pass mapping.
         
         # Assuming convert_module.convert_to_actual_import accepts (data, mapping)
         # If not, let's update it in next step. For now, calling with expected signature correction.
         converted = convert.convert_to_actual_import(transactions_list, self._config.get("accounts_mapping", {}))
         
         logger.info("Fetching Actual's token...")
         loop = asyncio.get_event_loop()
         
         # Custom init_actual that uses our config
         actual_config = {
             "url": self._config["actual_url"],
             "password": self._config["actual_password"],
             "budget_id": self._config["actual_budget_id"],
             "budget_password": self._config.get("actual_budget_password")
         }
         
         actual_token = await loop.run_in_executor(None, lambda: actual.init_actual(actual_config))
         
         if not actual_token:
             raise Exception("Failed to get Actual Budget token")

         logger.info("Importing data to Actual...")
         for account, transactions in converted.items():
            await loop.run_in_executor(None, lambda: actual.import_transactions(actual_token, account, transactions, actual_config["url"]))
         
         self._set_status(AppStatus.SUCCESS)

banking_service = BankingService()
