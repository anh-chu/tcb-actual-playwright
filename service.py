import asyncio
import json
import logging
from enum import Enum
from typing import Optional
from playwright.async_api import async_playwright, Playwright, Page, Browser, BrowserContext, expect
from modules import convert, actual
from modules.config import TCB_USERNAME, TCB_PASSWORD
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

    async def start_sync(self):
        if self._running:
            raise Exception("Sync already in progress")
        self._running = True
        # Fire and forget the main process, but we need to track it
        asyncio.create_task(self._run_process())

    async def stop_sync(self):
        self._running = False

    def _set_status(self, status: AppStatus):
        self._status = status
        logger.info(f"Status changed to: {status}")

    async def _run_process(self):
        screenshot_task = None
        try:
            self._set_status(AppStatus.STARTING)
            async with async_playwright() as self._playwright:
                self._browser = await self._playwright.chromium.launch(
                    headless=True, # We can run headless now as we take screenshots manually
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

                await self._process_login()
                
                if self._running:
                    await self._process_fetch()

        except Exception as e:
            logger.error(f"Error during sync: {e}")
            self._last_error = str(e)
            self._set_status(AppStatus.ERROR)
        finally:
            self._running = False
            if screenshot_task:
                screenshot_task.cancel()
                
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
        await self._page.locator("#username").fill(TCB_USERNAME)
        await self._page.locator("#password").click()
        await self._page.locator("#password").fill(TCB_PASSWORD)
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
        if not self._running: return
        self._set_status(AppStatus.FETCHING_DATA)
        
        cookies = await self._page.context.cookies()
        token = next((x["value"] for x in cookies if x["name"] == "Authorization" and "onlinebanking.techcombank.com.vn" in x["domain"]), None)
        
        if not token:
            raise Exception("Could not find Authorization token in cookies")
        
        import datetime
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        month_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting data from {month_ago} to {today}")
        url = f"https://onlinebanking.techcombank.com.vn/api/transaction-manager/client-api/v2/transactions?bookingDateGreaterThan={month_ago}&bookingDateLessThan={today}&from=0&size=500&orderBy=bookingDate&direction=DESC"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.7,vi;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://onlinebanking.techcombank.com.vn/",
            "Authorization": f"Bearer {token}",
        }
        
        response = await self._page.request.get(url=url, headers=headers)
        if response.status != 200:
             text = await response.text()
             raise Exception(f"Fetch failed with status {response.status}: {text}")
        
        data = await response.text()
        await self._process_save(data)

    async def _process_save(self, data_str: str):
         self._set_status(AppStatus.SAVING_DATA)
         # JSON processing is CPU bound, keep it sync or use run_in_executor if massive
         # For this size, sync is fine
         data_json = json.loads(data_str)
         
         logger.info("Converting data...")
         converted = convert.convert_to_actual_import(data_json)
         
         logger.info("Fetching Actual's token...")
         # actual.init_actual is sync (urllib), we should probably run it in executor to avoid blocking loop
         # But for simplicity let's leave as is or wrap it
         loop = asyncio.get_event_loop()
         actual_token = await loop.run_in_executor(None, actual.init_actual)
         
         if not actual_token:
             raise Exception("Failed to get Actual Budget token")

         logger.info("Importing data to Actual...")
         for account, transactions in converted.items():
            await loop.run_in_executor(None, lambda: actual.import_transactions(actual_token, account, transactions))
         
         self._set_status(AppStatus.SUCCESS)

banking_service = BankingService()
