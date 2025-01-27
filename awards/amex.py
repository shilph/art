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

    # log in
    page.goto("https://www.americanexpress.com/")
    page.wait_for_timeout(3000)
    page.get_by_role("link", name="Log In").click()
    page.wait_for_timeout(3000)
    page.get_by_test_id("userid-input").fill(account_info["username"])
    page.get_by_test_id("password-input").fill(account_info["password"])
    page.get_by_test_id("submit-button").click()
    page.wait_for_timeout(5000)

    # main page
    ###sec = next((page.query_selector_all("div.nav")), None).query_selector_all("section")[0]
    sec = page.query_selector("div.nav").query_selector("section")
    sec.click()
    # find cards only
    card_accounts = next((sel for sel in page.query_selector_all('ul') if "ACCOUNTS" in sel.inner_text()), None)
    cards = [
        card for card in card_accounts.query_selector_all('div')
        if "Card" in card.inner_text() and card.get_attribute('id') is not None
    ]
    card_names = [card.inner_text().replace('\n', '') for card in cards]
    sec.click()

    # run each card
    for card_name in card_names:
        sec.click()
        card_accounts = next((sel for sel in page.query_selector_all('ul') if "ACCOUNTS" in sel.inner_text()), None)
        cards = [
            card for card in card_accounts.query_selector_all('div')
            if "Card" in card.inner_text() and card.get_attribute('id') is not None
        ]
        card = next((card for card in cards if card_name == card.inner_text().replace('\n', '')), None)
        card.click()
        page.wait_for_timeout(5000)
        for div_row in page.query_selector_all("div.row"):
            if "Hilton" not in card_name and "Delta" not in card_name:
                regex = re.search(
                    r"Membership Rewards® Points\s+(?P<pts>[\d+,]+)\s+Explore Rewards$",
                    div_row.inner_text()
                )
                if regex is not None:
                    award_data["balance"] = int(regex.group('pts').replace(',', ''))

    # sign out
    page.goto("https://www.americanexpress.com/en-us/account/logout")
    page.wait_for_timeout(2000)
    page.close()

    return award_data
