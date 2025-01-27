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

    page.goto("https://www.ihg.com/")
    page.wait_for_timeout(3000)

    # log in
    next(
        (a for a in page.query_selector_all("a.logIn-link")
            if "Sign in" in a.inner_text() and a.is_visible()),
        None
    ).click()
    page.wait_for_timeout(3000)
    login_form = page.query_selector("div.login_modal").query_selector("form")
    input_id = login_form.query_selector("input[data-gigya-name='loginID']")
    input_id.click()
    input_id.fill(account_info['username'])
    input_password = login_form.query_selector("input[type='password']")
    input_password.click()
    input_password.fill(account_info['password'])
    next(
        (signin for signin in login_form.query_selector_all("input[type='submit']")
            if signin.get_attribute("value") == "Sign in"),
        None
    ).click()
    page.wait_for_timeout(3000)

    next(
        (x for x in page.query_selector_all("a.logIn-link")
            if x.is_visible() and x.inner_text() != "Sign out"),
        None
    ).click()
    page.wait_for_timeout(5000)
    text = page.query_selector("div.right-container").inner_text()
    award_data["balance"] = int(
        re.search(r"\s(?P<points>[\d,]+)\s", text).group("points").replace(",", "")
    )

    # IHG points expires in 12 month os inactivity for NON-ELITE member.
    sid = page.query_selector("span[data-slnm-ihg='memberLevelNameSID']")
    if not sid.is_visible() or "Elite" not in sid.inner_text():
        # Non-Elite members
        next(
            (a for a in page.query_selector("div.sub-nav-wrapper").query_selector_all("a")
                if a.inner_text() == "Account Activity" and a.is_visible()),
            None
        ).click()
        page.wait_for_timeout(5000)
        activities = page.query_selector("app-account-activities").query_selector_all("div.row")[2:]
        last_activity_date = datetime.strptime(
            next(
                (act.inner_text().splitlines()[0] for act in activities
                    if re.search(r"\s0 pts$", act.inner_text()) is None),
                None
            ),
            "%m/%d/%Y"
        )
        award_data["expire_date"] = last_activity_date + relativedelta( months=award_info["expire"])

    # logout
    if page.query_selector_all("div.logIn")[0].is_visible():
        # desktop mode
        next(
            (a for a in page.query_selector("div.logIn").query_selector_all("a")
                if a.inner_text() == "Sign out"),
            None
        ).click()
    else:
        # mobile mode
        page.query_selector("div.mobileNav").click()
        page.wait_for_timeout(3000)
        next(
            (li for li in page.query_selector_all("li.mobileNavMenu-list-item")[::]
                if li.inner_text() == "Sign out"),
            None
        ).click()

    page.wait_for_timeout(5000)
    page.close()

    return award_data
