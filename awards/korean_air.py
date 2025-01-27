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

    # Location: USA, Language: English
    page.goto("https://www.koreanair.com/us/en")
    page.wait_for_timeout(3000)

    # log in
    next(
        (button for button in page.query_selector_all("kc-button") if button.inner_text() == "Log in"),
        None
    ).click()
    page.wait_for_timeout(3000)
    page.query_selector("ke-text-input").click()
    page.query_selector("ke-text-input").query_selector("input").fill(account_info["username"])
    page.query_selector("ke-password-input").click()
    page.query_selector("ke-password-input").query_selector("input").fill(account_info["password"])
    next(
        (button for button in page.query_selector("form").query_selector_all("button")
            if "Log in" == button.inner_text()),
        None
    ).click()
    page.wait_for_timeout(3000)

    # go to my profile
    page.goto("https://www.koreanair.com/my-mileage/overview")
    page.wait_for_timeout(7000)
    earned = page.query_selector_all("span.mileage-my__point")[0].inner_text()
    award_data["balance"] = int(
        re.search(r"(?P<miles>[\d,]+)\s*Miles",earned).group("miles").replace(",", "")
    )

    # find mile validity
    if award_data["balance"] > 0:
        next(
            (button for button in page.query_selector_all("button")
                if button.inner_text() == "Mileage per valid period"),
            None
        ).click()
        expire_month = page.query_selector("table").query_selector_all("tr")[1].query_selector("th").inner_text()
        award_data["expire_date"] = datetime.strptime(expire_month, "%Y.%m")

    # log out
    page.goto("https://www.koreanair.com")
    page.wait_for_timeout(3000)
    page.query_selector("ul.headers__utils--list").query_selector_all("li")[1].click()
    page.wait_for_timeout(3000)
    page.query_selector("button[id='my-tooltip-logout-btn']").click()

    page.wait_for_timeout(2000)
    page.close()

    return award_data
