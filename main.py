import time
import re
import json
import os
import datetime
from zoneinfo import ZoneInfo

from playwright.sync_api import (
    Playwright,
    sync_playwright,
    expect,
    BrowserContext,
    Page,
    Browser,
)

from modules import convert, actual
from modules.logger import logger
from modules.config import TCB_USERNAME, TCB_PASSWORD


def login(context: BrowserContext):
    page = context.new_page()

    logger.info("Logging in...")

    page.goto("https://onlinebanking.techcombank.com.vn/dashboard")

    expect(page.locator("#username")).to_be_visible()

    page.locator("#username").fill(TCB_USERNAME)
    page.locator("#password").click()
    page.locator("#password").fill(TCB_PASSWORD)
    page.locator("#kc-login").click()

    logger.info("Waiting for OTP...")

    # expect(page.get_by_role("heading", name="Back Please check your device").or_(page.get_by_text("Auto-Earning Balance"))).to_be_visible()
    expect(page.locator(".user-context-menu-info__container__name")).to_be_attached(
        timeout=90000
    )

    logger.info("Logged in successfully!")

    return page


def fetch_data(token: str, page: Page):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    month_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime(
        "%Y-%m-%d"
    )

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

    response = page.request.get(url=url, headers=headers)

    logger.info(f"Got data from {month_ago} to {today}!")

    return response.status, response.text()


def save_data(data: str):
    # with open("data.json", "w") as f:
    #     f.write(data)
    logger.info("Converting data to Actual import...")

    converted = convert.convert_to_actual_import(json.loads(data))

    logger.info("Fetching Actual's token...")
    actual_token = actual.init_actual()

    logger.info("Importing data to Actual...")

    for account, transactions in converted.items():
        r = actual.import_transactions(actual_token, account, transactions)
        # print(r)

    logger.info("Done!")


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(
        headless=False,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1280,800",
        ],
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    )

    page = login(context)

    page.screenshot(path="screenshots/screenshot.png")

    cookies = page.context.cookies()
    token = [
        x
        for x in cookies
        if x["name"] == "Authorization"
        and x["domain"] == "onlinebanking.techcombank.com.vn"
    ][0]["value"]

    (status, data) = fetch_data(token, page)

    match status:
        case 200:
            save_data(data)
        case 401:
            logger.error(status)
        case _:
            logger.error(status)
            logger.error(data)

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
