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

"""
loop A:
    get api
    if 200:
        ingest
    if 401:
        login
        if error:
            notify
            wait for re-trigger

re-trigger received:
    run loop A

"""

READY = False


def login(context: BrowserContext):
    page = context.new_page()

    logger.info("Logging in...")

    page.goto("https://onlinebanking.techcombank.com.vn/dashboard")

    expect(page.locator("#username")).to_be_visible()

    page.locator("#username").fill("0828041168")
    page.locator("#password").click()
    page.locator("#password").fill("AH253490sil")
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
    global READY
    browser = playwright.chromium.launch()
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
    )

    while not READY:
        d = datetime.datetime.now(ZoneInfo(os.getenv("TZ", "Asia/Ho_Chi_Minh")))
        if d.hour > 22 or d.hour < 9:
            logger.warning("Night time, sleeping for 1 hour...")
            time.sleep(60 * 60)
            continue
        try:
            page = login(context)
            READY = True
        except Exception as e:
            logger.error(e)
            time.sleep(60 * 15)

    while READY:
        counter = 1
        # get auth from cookies
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
                READY = True
                save_data(data)
            case 401:
                READY = FALSE
                print(status)
            case _:
                print(status)
                print(data)

        while counter < 45:  # every 15 minutes
            # keep page alive
            page.goto("https://onlinebanking.techcombank.com.vn/accounts")
            time.sleep(10)
            page.goto("https://onlinebanking.techcombank.com.vn/dashboard")
            time.sleep(10)
            counter += 1

    page.screenshot(path="screenshots/screenshot.png")

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
