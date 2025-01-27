"""This is a quick script to test an award script.

How to use:
    python _awards_script_test.py <script name> <arg> <arg> ...
        arg: (account_info field name)=(value)
             Please use an equal sign (=).
    i.e. python _awards_script_test.py amex username=amex_username password=amex_password
"""

from importlib import import_module
import sys

if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    from random import randint
    from subprocess import Popen

    port = randint(10000, 30000)
    print(f"Chrome debug port: {port}")
    Popen([r"C:\Program Files\Google\Chrome\Application\chrome.exe",
           f"--remote-debugging-port={port}",
           "--window-size=1024,800"])
    playwright = sync_playwright().start()
    browser = playwright.chromium.connect_over_cdp(f"http://localhost:{port}")

    script = import_module(sys.argv[1])
    account_info = {}
    for arg in sys.argv[2:]:
        account_info[arg.split("=")[0]] = arg.split("=")[1]
    # use a dummy expire date
    award_info = {"expire": 12}
    print(
        script.get_balance(browser=browser, account_info=account_info, award_info=award_info)
    )
    browser.close()
    playwright.stop()
