# Copy-Item "C:\Users\USERNAME\AppData\Local\Google\Chrome\User Data" "C:\Users\USERNAME\automation-profile" -Recurse
# Replace USERNAME with your actual username
# Copy-Item "C:\Users\hurai\AppData\Local\Google\Chrome\User Data" "C:\Users\hurai\auto2" -Recurse
# & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\USERNAME\automation-profile" --profile-directory="Profile 4"
# Replace Profile 4 with the name of the profile you want to use
# Install the Helium 10 extension from the Chrome Web Store
# Pin the Helium 10 icon to the toolbar
# Run this Python script


# & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\hurai\automation-profile" --profile-directory="Profile 4"


from playwright.sync_api import sync_playwright
import time

CDP_URL = "http://127.0.0.1:9222"
AMAZON_URL = "https://www.amazon.com/s?k=cricket+bat&crid=1ZCPCQZN6DZSY&sprefix=cricket+%2Caps%2C665&ref=nb_sb_noss_2"
EXT_ID = "njmehopjdpcckochcggncklnlmikcbnb"
POPUP_URL = f"chrome-extension://{EXT_ID}/popup.html"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    page = context.new_page()

    # Search on Amazon
    page.goto("https://www.amazon.com/s?k=hand+wipe")
    # page.wait_for_load_state("networkidle")

    # Access Chrome DevTools Protocol directly
    client = context.new_cdp_session(page)


    input("Press Enter to close...")


