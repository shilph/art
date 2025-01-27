import re


def get_balance(browser, account_info: dict, **kwargs) -> dict:
    """Get the current points/mileage balance and expected expire date.

    :param browser: Chrome debug browser (Playwright)
    :param account_info: account information from database
    :return: current points/mileages balance, expected expire date (None for not expired or unknonw)
    """

    context = browser.contexts[0]
    page = context.new_page()
    award_data = {"balance": 0, "expire_date": None}

    page.goto("https://www.delta.com")
    page.wait_for_timeout(3000)

    # I noticed Delta page has an unexpected popup message.
    for err_tt in page.query_selector_all("div.idp-error-tooltip"):
        if err_tt.is_visible():
            if err_tt.query_selector("button") is not None:
                err_tt.click()

    page.query_selector("button[id='login-modal-button']").click()
    page.wait_for_timeout(3000)
    form = page.query_selector("idp-login-authentication-screen").query_selector("form")
    inputs = form.query_selector_all("idp-input")
    inputs[0].click()
    inputs[0].query_selector("input").fill(account_info["username"])
    inputs[1].click()
    inputs[1].query_selector("input").fill(account_info["password"])
    page.wait_for_timeout(1000)
    form.query_selector("idp-button").click()
    page.wait_for_timeout(5000)

    page.goto("https://www.delta.com/myskymiles/overview")
    page.wait_for_timeout(5000)
    text = page.query_selector("idp-skymiles-overview").query_selector("idp-overview-summary").inner_text()
    award_data["balance"] = int(
        re.search(r"\s+(?P<miles>[\d,]+)\s+MILES AVAILABLE", text).group("miles").replace(",","")
    )

    header_sec = [
        div for div in page.query_selector("nav").query_selector_all("div")
        if div.get_attribute("class") is not None and div.get_attribute("class").startswith("d-flex")
    ][0]
    header_sec.query_selector("ngc-login").click()
    page.wait_for_timeout(3000)
    page.query_selector("div[class='modal-content']").query_selector_all("div")[-1].click()
    page.wait_for_timeout(5000)

    page.close()

    return award_data
