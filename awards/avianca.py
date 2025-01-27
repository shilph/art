import re
from datetime import datetime


def get_balance(browser, account_info: dict, award_info: dict, **kwargs) -> dict:
    """Get the current points/mileage balance and expected expire date.

    :param browser: Chrome debug browser (Playwright)
    :param account_info: account information from database
    :param award_info: award information from database
    :return: current points/mileages balance, expected expire date (None for not expired or unknonw)
    """

    context = browser.contexts[0]
    page = context.new_page()
    award_data = {"balance": 0, "expire_date": None}

    page.goto("https://www.lifemiles.com/account/overview")
    page.wait_for_timeout(5000)

    # log in
    page.query_selector("a#social-Lifemiles").click()
    page.wait_for_timeout(5000)
    username_input = page.query_selector_all("div.authentication-ui-Lifemiles_inputMargin")[0]
    username_input.click()
    username_input.query_selector("input").fill(account_info["username"])
    password_input = page.query_selector_all("div.authentication-ui-Lifemiles_inputMargin")[1]
    password_input.click()
    password_input.query_selector("input").fill(account_info["password"] )
    page.wait_for_timeout(1000)
    username_input.click()
    page.query_selector("button#Login-confirm").click()
    page.wait_for_timeout(10000)

    # get mileage balance and expire date
    text = page.query_selector("div[data-cy='OverviewTitleTxt']").inner_text()
    award_data["balance"] = int(
        re.search(r"\s(?P<miles>[\d,]+)$", text).group("miles").replace(",", "")
    )
    award_data["expire_date"] = datetime.strptime(
        page.query_selector("div[data-cy='OverviewPointsExpirationDateTxt']").inner_text().split(":")[1].strip(),
        "%b %d, %Y"
    )
    page.wait_for_timeout(3000)

    # log out
    page.query_selector("div.menu-ui-Menu_button").click()
    page.wait_for_timeout(1000)
    page.query_selector("div#ProfileTooltipId").query_selector("button").click()
    page.wait_for_timeout(5000)
    page.close()

    return award_data
