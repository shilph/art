def get_balance(browser, account_info: dict, **kwargs) -> dict:
    """Get the current points/mileage balance and expected expire date.

    :param browser: Chrome debug browser (Playwright)
    :param account_info: account information from database
    :return: current points/mileages balance, expected expire date (None for not expired or unknonw)
    """

    context = browser.contexts[0]
    page = context.new_page()
    award_data = {"balance": 0, "expire_date": None}

    page.goto("https://www.southwest.com/")
    page.wait_for_timeout(3000)

    # log in
    login_button = next(
        (div for div in page.query_selector("div.header-control").query_selector_all("button")
            if "Log in" in div.inner_text()),
        None
    )
    login_button.click()
    login_form = page.query_selector("div.overlay-container").query_selector_all("form")[0]
    login_form.query_selector_all("input")[0].click()
    login_form.query_selector_all("input")[0].fill(account_info["username"])
    login_form.query_selector_all("input")[1].click()
    login_form.query_selector_all("input")[1].fill(account_info["password"])
    login_form.query_selector("button").click()
    page.wait_for_timeout(5000)

    page.goto("https://www.southwest.com/account")

    retry = 0
    while retry < 3:
        # available credits and points
        page.wait_for_timeout(3000)
        points_and_credits = [
            span for span in page.query_selector_all("span")
            if span.get_attribute("class") is not None
               and span.get_attribute("class").startswith("pointsAndTravelCredits_")
        ]
        if len(points_and_credits) > 0:
            award_data["balance"] = int(
                points_and_credits[0].query_selector_all("span[aria-hidden='true']")[1].inner_text().replace(",", "")
            )
            # for future use: available credits ($)
            award_data["credit"] = float(
                points_and_credits[0].query_selector_all("span[aria-hidden='true']")[0].inner_text().replace("$", "")
            )
            break
        retry += 1

    # log out
    next((button for button in page.query_selector_all("button") if button.inner_text() == "Log out"), None).click()
    page.wait_for_timeout(3000)
    page.close()

    return award_data
