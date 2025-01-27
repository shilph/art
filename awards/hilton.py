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

    page.goto("https://www.hilton.com/")
    page.wait_for_timeout(3000)

    # login : Hilton uses iframe
    next(
        (button for button in page.query_selector_all("button")
            if button.inner_text() == "Sign In" and button.is_visible()),
        None
    ).click()
    page.wait_for_timeout(2000)
    frame = next(
        (frame for frame in page.frames if frame.url == "https://www.hilton.com/en/auth2/guest/login/"),
        None
    )
    inputs = frame.query_selector_all("input")
    inputs[0].click()
    inputs[0].fill(account_info["username"])
    inputs[1].click()
    inputs[1].fill(account_info["password"])
    next((button for button in frame.query_selector_all("button")
          if button.inner_text() == "Sign In"), None).click()
    page.wait_for_timeout(5000)

    # go to activity
    page.goto("https://www.hilton.com/en/hilton-honors/guest/activity/")
    page.wait_for_timeout(10000)
    containers = page.query_selector("main").query_selector_all("div.container-fluid")
    award_data["balance"] = int(
        [line for line in containers[0].inner_text().splitlines() if re.match(r"[\d,]+", line)][0].replace(",", "")
    )
    activities = containers[1].query_selector("section").query_selector_all("div")
    last_act = None
    for act in containers[1].query_selector("section").query_selector_all("div"):
        text = act.inner_text()
        if "Points" in text and "through" in text and "again" not in text and re.search(r"\n0$",text) is None \
                and re.search(r"[+-]+\s*\d+$", text) is not None:
            last_act = text
            break
    if last_act is not None:
        last_date = datetime.strptime(re.findall(r"\w+ \d{1,2}, \d{4}", last_act)[1], "%B %d, %Y")
        award_data["expire_date"] = last_date + relativedelta(months=award_info["expire"])

    # log out
    next((button for button in page.query_selector_all("button") if "Hi, " in button.inner_text()), None).click()
    page.wait_for_timeout(1000)
    next((button for button in page.query_selector_all("button") if "Sign Out" in button.inner_text()), None).click()
    page.wait_for_timeout(2000)
    page.close()

    return award_data
