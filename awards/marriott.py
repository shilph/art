import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tkinter import simpledialog


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

    page.goto("https://www.marriott.com/signInOverlay.mi")
    page.wait_for_timeout(3000)
    try:
        login_frame = next(
            (frame for frame in page.frames if frame.url == "https://www.marriott.com/signInOverlay.mi?overlay=true"),
            None
        )
        login_frame.query_selector("button[aria-label='Sign in with different account']").click()
        page.wait_for_timeout(3000)
    except AttributeError:
        # there is no save account info. Just login
        pass

    # log in
    login_frame = next(
        (frame for frame in page.frames if frame.url == "https://www.marriott.com/signInOverlay.mi?overlay=true"),
        None
    )
    login_form = login_frame.query_selector("form")
    login_form.query_selector_all("input")[0].click()
    login_form.query_selector_all("input")[0].fill(account_info["username"])
    login_form.query_selector_all("input")[1].click()
    login_form.query_selector_all("input")[1].fill(account_info["password"])
    # Marriott page has a misspelled component. oh....
    if login_form.query_selector_all("div.form-field-contaioner")[2].query_selector("input").is_checked():
        login_form.query_selector_all("div.form-field-contaioner")[2].click()
        page.wait_for_timeout(1000)
    login_form.query_selector("button").click()
    page.wait_for_timeout(5000)

    # Marriott may ask you for 2nd authentication
    if "Email code to" in page.query_selector("main").inner_text():
        next(
            (div for div in page.query_selector_all("div[data-component-name='a-ui-library-RadioButton']")
                if "Email code to" in div.inner_text()),
            None
        ).query_selector("label").click()
        page.query_selector("div.confirm-identity-container").query_selector("button").click()
        # get code
        passcode = simpledialog.askstring(
            "Identity Verification", "Please enter passcode from Marriott to your email:"
        )
        passcode_input = page.query_selector("input[type='number']")
        passcode_input.click()
        passcode_input.fill(passcode)
        page.query_selector("button[data-testid='verify-button']").click()
        page.wait_for_timeout(5000)

    # account info
    page.goto("https://www.marriott.com/loyalty/myAccount/activity.mi")
    page.wait_for_timeout(5000)
    award_data["balance"] = int(
        next(
            (line for line in page.query_selector("div.container__left--points").inner_text().splitlines()
                if re.match(r"[\d,]+", line.strip())),
            None
        ).replace(",", "")
    )
    # find the last activity
    for div in page.query_selector_all("div[role='row']"):
        regex = re.search(r"(?P<points>[\d,]+)\s+Points", div.inner_text())
        if regex is not None and int(regex.group("points").replace(",", "")) != 0:
            last_date = datetime.strptime(div.inner_text().splitlines()[0],"%b %d, %Y")
            award_data["expire_date"] = last_date + relativedelta(months=award_info["expire"])

    # logout
    page.query_selector("li.m-header__acnt").click()
    page.query_selector("a.mp__member-logout").click()
    page.wait_for_timeout(3000)
    page.close()

    return award_data
