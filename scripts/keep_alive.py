"""Keep the Streamlit Community Cloud app awake.

Community Cloud puts idle apps to sleep and serves a "wake up" page instead.
A plain HTTP ping doesn't wake it, so this opens the app in a headless browser
and clicks the wake-up button when it shows up.
"""

import re
import sys

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

APP_URL = "https://pix-analytics-portfolio.streamlit.app/"
WAKE_BUTTON = re.compile(r"get this app back up", re.IGNORECASE)


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(APP_URL, wait_until="domcontentloaded", timeout=60_000)

        # The app itself renders inside an iframe, so look in every frame.
        page.wait_for_timeout(15_000)
        button = None
        for frame in page.frames:
            candidate = frame.get_by_role("button", name=WAKE_BUTTON)
            try:
                candidate.first.wait_for(timeout=2_000)
                button = candidate.first
                break
            except PlaywrightTimeout:
                continue

        if button is None:
            print("App is awake, nothing to do.")
            browser.close()
            return 0

        print("App was asleep, clicking wake-up button.")
        button.click()
        # Give the container time to boot before the browser goes away.
        page.wait_for_timeout(90_000)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
