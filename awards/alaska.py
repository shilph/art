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
    page.goto("https://www.alaskaair.com")
    page.wait_for_timeout(3000)

    if page.query_selector("ul.top-menu-list").is_visible():
        # desktop mode
        top_menu_list = page.query_selector("ul.top-menu-list")
        next((li for li in top_menu_list.query_selector_all("li") if "Sign in" in li.inner_text()), None).click()
        inputs = [
            i for i in top_menu_list.query_selector("form").query_selector_all("input")
            if i.get_attribute("type") != "hidden"
        ]
        page.wait_for_timeout(1000)
        inputs[0].click()
        inputs[0].fill(account_info["username"])
        page.wait_for_timeout(2000)
        inputs[1].click()
        inputs[1].fill(account_info["password"])
        top_menu_list.query_selector("form").query_selector("button").click()
        page.wait_for_timeout(3000)

        award_data["balance"] = int(
            page.query_selector("div.mp-info").inner_text().splitlines()[0].split(":")[1].strip().replace(",", "")
        )
        # logout
        top_menu_list = page.query_selector("ul.top-menu-list")
        account_menu = next(
            (li for li in top_menu_list.query_selector_all("li") if "Hi, " in li.inner_text()),
            None
        )
        account_menu.click()
        page.wait_for_timeout(1000)
        account_menu.query_selector_all("li")[-1].query_selector("a").click()
    else:
        page.query_selector("div[data-testid='HeaderMobile']")\
            .query_selector("div#hf-nav-top")\
            .query_selector_all("li")[2].click()
        mob_menu = page.query_selector("div.nav-mobile-menu")
        next((s for s in mob_menu.query_selector_all("li")
              if "Sign in/Sign up" == s.inner_text()), None).click()
        page.wait_for_timeout(1000)
        mob_menu.query_selector("input[name='UserId']").click()
        mob_menu.query_selector("input[name='UserId']").fill(account_info["username"])
        page.wait_for_timeout(1000)
        mob_menu.query_selector("input[name='Password']").click()
        mob_menu.query_selector("input[name='Password']").fill(account_info["password"])
        page.wait_for_timeout(1000)
        if mob_menu.query_selector("input[name='RememberMe']").is_checked():
            mob_menu.query_selector("input[name='RememberMe']").click()
        next(
            (button for button in mob_menu.query_selector_all("button") if button.inner_text() == "SIGN IN"),
            None
        ).click()
        page.wait_for_timeout(3000)

        award_data["balance"] = int(
            page.query_selector("div.mp-info").inner_text().splitlines()[0].split(":")[1].strip().replace(",", "")
        )
        # logout
        page.query_selector("div[data-testid='HeaderMobile']")\
            .query_selector("div#hf-nav-top")\
            .query_selector_all("li")[2].click()
        mob_menu = page.query_selector("div.nav-mobile-menu")
        next((s for s in mob_menu.query_selector_all("li") if s.inner_text().startswith("Hi,")), None).click()
        page.wait_for_timeout(2000)
        next((s for s in mob_menu.query_selector_all("li") if s.inner_text() == "Sign out"), None).click()

    page.wait_for_timeout(3000)
    page.close()

    return award_data
