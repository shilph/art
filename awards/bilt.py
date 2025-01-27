from tkinter import simpledialog
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

    page.goto("https://www.biltrewards.com/account")
    page.wait_for_timeout(3000)

    # log in: browser may go to login page directly
    login_selector = [q for q in page.query_selector_all("div") if "SIGN UP / LOG IN" == q.inner_text()]
    if len(login_selector) > 0:
        next((q for q in page.query_selector_all("div") if "SIGN UP / LOG IN" == q.inner_text()), None).click()
        page.wait_for_timeout(3000)
    next((q for q in page.query_selector_all("div") if "Email" == q.inner_text()), None).click()
    page.wait_for_timeout(3000)
    username_input = next((q for q in page.query_selector_all("div") if "Your email" == q.inner_text()), None)
    username_input.click()
    username_input.query_selector("input").fill(account_info["email"])
    next((q for q in page.query_selector_all("div") if "Next" == q.inner_text()), None).click()

    # log in with email
    passcode = simpledialog.askstring(title="Login with email",
                                      prompt="Please enter passcode from Bilt to your email:")
    ###passcode_inputs = next((page.query_selector_all("form")), None).query_selector_all("input")
    passcode_inputs = page.query_selector("form").query_selector_all("input")
    for index in range(0, len(passcode_inputs)):
        passcode_inputs[index].click()
        passcode_inputs[index].fill(passcode[index])
    page.wait_for_timeout(5000)

    # expect that account is still logged in
    for a in page.query_selector_all("a"):
        text = a.inner_text()
        if "points" in text and "Your status" in text:
            award_data["balance"] = int(
                re.search(r"\s(?P<points>[\d,]+) points",text).group("points").replace(",", "")
            )

    # logout
    [a for a in page.query_selector_all("a") if a.get_attribute("href") == "/logout"][-1].click()
    page.wait_for_timeout(3000)
    next((button for button in page.query_selector_all("button") if button.inner_text() == "Logout"), None).click()
    page.wait_for_timeout(3000)
    page.close()

    return award_data
