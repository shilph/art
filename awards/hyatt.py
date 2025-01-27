import re
from datetime import datetime
from dateutil.relativedelta import relativedelta


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

    page.goto("https://www.hyatt.com/")
    page.wait_for_timeout(3000)

    # log in
    page.query_selector("div[data-locator='account-panel']").click()
    page.wait_for_timeout(3000)
    next((form for form in page.query_selector_all("form")if "SIGN IN" in form.inner_text()), None).click()
    page.wait_for_timeout(2000)
    next(
        (form for form in page.query_selector_all("div.signin-with-pwd-button")
            if "SIGN IN WITH PASSWORD" in form.inner_text()),
        None
    ).click()
    page.wait_for_timeout(2000)
    signin_form = page.query_selector("form[name=signin-form]")
    userid_input = signin_form.query_selector("input[name=userId]")
    userid_input.click()
    userid_input.fill(account_info["username"])
    lastname_input = signin_form.query_selector("input[name=lastName]")
    lastname_input.click()
    lastname_input.fill(account_info["lastname"])
    password_input = signin_form.query_selector("input[name=password]")
    password_input.click()
    password_input.fill(account_info["password"])
    next((div for div in signin_form.query_selector_all("div") if "SIGN IN" == div.inner_text()), None).click()
    page.wait_for_timeout(1000)
    page.query_selector("div[data-locator=account-panel]").click()

    # get balance info
    page.goto("https://www.hyatt.com/profile/en-US/account-overview")
    page.wait_for_timeout(3000)
    for div in page.query_selector_all("div"):
        balance = re.search(r"Current Point Balance\s+(?P<bal>[\d+,]+)\s*$", div.inner_text())
        if balance is not None:
            award_data["balance"] = int(balance.group("bal").replace(",", ""))
            break
        else:
            balance = re.search(r"(?P<bal>[\d+,]+)\s+Current Point Balance",div.inner_text())
            if balance is not None:
                award_data["balance"] = int(balance.group("bal").replace(",", ""))
                break

    # get the latest activity
    page.goto("https://www.hyatt.com/profile/en-US/account-activity")
    retry = 0
    while retry < 3:
        page.wait_for_timeout(5000)
        tranactions = page.query_selector_all("div[data-js='transactions']")
        if tranactions is not None:
            all_activities = tranactions[0].query_selector_all("div.b-mb2")
            if len(all_activities) > 0:
                for act in all_activities:
                    act_info = act.inner_text()
                    regex = re.search(r"Points\s+(?P<points>[-\d,]+)", act_info)
                    if regex is not None:
                        points = int(regex.group("points").replace(",", ""))
                        if points != 0:
                            # get date
                            act_date = re.search(
                                r"\s(?P<act_date>[A-Za-z]{3}\s+\d{1,2},\s+\d{4})\s+", act_info
                            ).group("act_date")
                            award_data["expire_date"] = datetime.strptime(act_date, "%b %d, %Y") \
                                                        + relativedelta( months=award_info["expire"])
                            page.query_selector("div[data-locator='account-panel']").click()

                            page.query_selector("div.hbe-header_profile-signout").click()
                            page.wait_for_timeout(2000)
                            page.close()

                            return award_data
        retry += 1
        print(f"Hyatt: could not get div[data-js='transactions']: Try #{retry}")

    page.query_selector("div[data-locator='account-panel']").click()

    page.query_selector("div.hbe-header_profile-signout").click()
    page.wait_for_timeout(2000)
    page.close()

    return award_data
