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

    page.goto("https://www.aa.com")
    page.wait_for_timeout(3000)

    # log in
    try:
        next(
            (button for button in page.query_selector_all("hp-header-button")
                if button.inner_text() == "Log in" and button.is_visible()),
            None
        ).click()
        page.wait_for_timeout(3000)
    except AttributeError:
        # log out if previously logged in
        dropdown = next(
            (dropdown for dropdown in page.query_selector_all("adc-account-dropdown") if dropdown.is_visible()),
            None
        )
        dropdown.click()
        page.wait_for_timeout(1000)
        next(
            (button for button in dropdown.query_selector_all("hp-account-dropdown-button")
                if button.is_visible() and button.inner_text() == "Log out"),
            None
        ).click()
        page.wait_for_timeout(3000)
        # log in again
        next(
            (button for button in page.query_selector_all("hp-header-button")
             if button.inner_text() == "Log in" and button.is_visible()),
            None
        ).click()
        page.wait_for_timeout(3000)

    input_username = page.query_selector("ail-input#username")
    input_username.click()
    input_username.query_selector("input").fill(account_info["username"])
    input_password = page.query_selector("ail-input#password")
    input_password.click()
    input_password.query_selector("input").fill(account_info["password"])
    page.query_selector("button#button_login").click()
    page.wait_for_timeout(5000)

    # go to account
    next(
        (button for button in page.query_selector_all("hp-account-dropdown-button") if button.is_visible()),
        None
    ).click()
    page.wait_for_timeout(2000)
    next(
        (button for button in page.query_selector_all("hp-account-dropdown-button")
            if button.is_visible() and button.inner_text() == "Personal account"),
        None
    ).click()
    page.wait_for_timeout(5000)
    text = page.query_selector("div[data-testid='award-miles-balance-text']").inner_text()
    award_data["balance"] = int(
        re.search(r"\s+(?P<miles>[\d,]+)\s+", text).group("miles").replace(",", "")
    )

    # AA mileages do not expire for AA credit card holders.
    text = page.query_selector("div[data-testid='award-miles-balance-section']").inner_text()
    if "no miles expiration" not in text:
        award_data["expire_date"] = datetime.strptime(
            re.search(r"expire on\s+(?P<expire_date>[A-Za-z]{3}\s+\d{1,2},\s+\d{4})", text).group("expire_date"),
            "%b %d, %Y"
        )

    if page.query_selector("li#headerCustomerInfo").is_visible():
        page.query_selector("li#headerCustomerInfo").query_selector("button").click()
        page.wait_for_timeout(2000)
        page.query_selector("li#headerCustomerInfo").query_selector("p#logout-button").click()
    else:
        page.query_selector("li#utilityCustomerInfo").query_selector("a").click()
        page.wait_for_timeout(2000)
        page.query_selector("li#utilityCustomerInfo").query_selector_all("a")[1].click()

    page.wait_for_timeout(5000)
    page.close()

    return award_data
