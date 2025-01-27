import re
from datetime import datetime


def get_balance(browser, account_info: dict, **kwargs) -> dict:
    """Get the current points/mileage balance and expected expire date.

    :param browser: Chrome debug browser (Playwright)
    :param account_info: account information from database
    :return: current points/mileages balance, expected expire date (None for not expired or unknonw)
    """

    context = browser.contexts[0]
    page = context.new_page()
    award_data = {"balance": 0, "expire_date": None}

    page.goto("https://www.united.com/us/en")
    page.wait_for_timeout(3000)

    # log in
    page.query_selector_all("nav")[1].query_selector_all("li")[2].click()
    # if the browser stores previously logged account information, click "switch account" button first.
    switch_account = next(
        (button for button in page.query_selector("div.atm-c-drawer__body").query_selector_all("button")
            if button.inner_text() == "Switch accounts" and button.is_visible()),
        None
    )
    if switch_account is not None:
        page.query_selector("div.atm-c-drawer__body").query_selector("input[type='checkbox']").click()
        switch_account.click()
        page.wait_for_timeout(2000)

    entry = page.query_selector("div.atm-c-drawer__body").query_selector("div.atm-c-textfield").query_selector("input")
    entry.click()
    entry.fill(account_info["username"])
    page.query_selector("div.atm-c-drawer__body").query_selector("button[type='submit']").click()
    page.wait_for_timeout(2000)
    entry = page.query_selector("div.atm-c-drawer__body").query_selector("div.atm-c-textfield").query_selector("input")
    entry.click()
    entry.fill(account_info["password"])
    page.query_selector("div.atm-c-drawer__body").query_selector("button[type='submit']").click()
    page.wait_for_timeout(3000)

    page.goto("https://www.united.com/en/us/myunited")
    page.wait_for_timeout(3000)
    award_data["balance"] = int(
        next(
            (div for div in page.query_selector("main").query_selector_all("div")
                if div.get_attribute("class") is not None and "totalMiles" in div.get_attribute("class")),
            None
        ).inner_text().replace(",", "")
    )
    page.wait_for_timeout(2000)

    # log out
    page.query_selector_all("nav")[1].query_selector_all("li")[2].click()
    page.query_selector("div.atm-c-drawer__body").query_selector("button").click()
    page.wait_for_timeout(5000)
    page.close()

    return award_data
