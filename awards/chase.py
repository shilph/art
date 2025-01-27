def get_balance(browser, account_info: dict, **kwargs) -> dict:
    """Get the current points/mileage balance and expected expire date.

    :param browser: Chrome debug browser (Playwright)
    :param account_info: account information from database
    :return: current points/mileages balance, expected expire date (None for not expired or unknonw)
    """

    context = browser.contexts[0]
    page = context.new_page()
    award_data = {"balance": 0, "expire_date": None}

    # directly go to Chase UR page
    page.goto("https://ultimaterewardspoints.chase.com")
    page.wait_for_timeout(5000)
    page.get_by_label("Username").fill(account_info["username"])
    page.get_by_label("Password").fill(account_info["password"])
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_timeout(5000)

    # select the first card of the list
    ###page.query_selector_all('li')[0].click()
    page.query_selector('li').click()
    page.wait_for_timeout(5000)

    # list all UR cards
    ur_cards = []
    for card in page.query_selector_all('div.list-item--selectable'):
        parsed = card.inner_text().split(',')
        ur_cards.append(parsed[1].strip())
    for card_name in ur_cards:
        card = next(
            (_card for _card in page.query_selector_all('div.list-item--selectable')
                if card_name in _card.inner_text()),
            None
        )
        page.query_selector('button.card-selector-button').click()
        card.click()
        page.get_by_role("button", name="Confirm").click()
        page.wait_for_timeout(5000)
        # find points balance
        points_balance = page.query_selector('div.points-balance').inner_text().splitlines()
        award_data["balance"] += int(points_balance[0].replace(',', ''))

    # sign out
    page.locator('text="Sign out"').click()
    page.wait_for_timeout(5000)
    page.close()

    return award_data
