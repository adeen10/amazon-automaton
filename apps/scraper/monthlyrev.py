# command to run chrome profile
# PS Adeen:C:\WINDOWS\system32> & "C:\Users\Al-Wajid Laptops\AppData\Local\Google\Chrome\Application\chrome.exe" `       
# >>   --remote-debugging-port=9666 `                                                                                    
# >>   --user-data-dir="C:\Users\Al-Wajid Laptops\automation-profile" `                                                  
# >>   --profile-directory="Profile 4" `                                                                                 
# >>   "https://google.com"  

# from playwright.sync_api import sync_playwright
# import time

# CDP_URL = "http://127.0.0.1:9222"
# AMAZON_PRODUCT_URL = "https://www.amazon.com/s?k=cricket+bat&crid=1ZCPCQZN6DZSY&sprefix=cricket+%2Caps%2C665&ref=nb_sb_noss_2"
# EXT_ID = "njmehopjdpcckochcggncklnlmikcbnb"
# POPUP_URL = f"chrome-extension://{EXT_ID}/popup.html"

# with sync_playwright() as p:
#     # Attach to your running Chrome (Profile 4 on 9666)
#     browser = p.chromium.connect_over_cdp(CDP_URL)

#     # Open the Amazon search page in this same window (optional seed tab)
#     ctx = browser.contexts[0]
#     seed = ctx.new_page()
#     seed.goto(AMAZON_PRODUCT_URL, wait_until="domcontentloaded")
#     print("[info] Opened Amazon search page.")

#     # Open Helium popup as a full tab (so we have chrome.* APIs)
#     popup = ctx.new_page()
#     popup.goto(POPUP_URL, wait_until="domcontentloaded")
#     print("[info] Opened Helium popup tab.")

#     # Ask Helium background to open the URL and trigger XRAY
#     # This uses the background message type from your extension code: "open-page-and-xray"
#     popup.evaluate(
#         """(targetUrl) => {
#             return new Promise((resolve) => {
#                 chrome.runtime.sendMessage(
#                     { type: "open-page-and-xray", params: { url: targetUrl } },
#                     () => resolve(true)
#                 );
#             });
#         }""",
#         AMAZON_PRODUCT_URL,
#     )
#     print("[info] Sent background message: open-page-and-xray")

#     # Wait for Helium to open/activate a tab to that URL (it may open a new tab)
#     target_page = None
#     for _ in range(20):  # up to ~10s
#         for pg in ctx.pages:
#             # Helium may add params; just check it’s an Amazon search page
#             if pg.url.startswith("https://www.amazon.com/s?"):
#                 target_page = pg
#                 break
#         if target_page:
#             break
#         time.sleep(0.5)

#     if target_page:
#         target_page.bring_to_front()
#         print("[SUCCESS] Amazon tab for XRAY is active. Helium should be running now.")
#     else:
#         print("[warn] Could not detect the Helium-opened Amazon tab. It might still be initializing.")

#     first_value = target_page.locator('[data-testid="table-cell-estMonthlyRevenue"]').first.inner_text()
#     print("Current Monthly Revenue (Parent Level Revenue of 1st product): ", first_value)

#     input("Press Enter to disconnect…")


# monthlyrev.py
import re
import time
from typing import Dict, Optional
from playwright.sync_api import Browser, Page

CURRENCY_RX = re.compile(r"^\$?\s*\d[\d,]*(?:\.\d+)?$")

def _pick_ctx(browser: Browser):
    return browser.contexts[0] if browser.contexts else browser.new_context()

def _close_all_tabs(browser: Browser) -> int:
    closed = 0
    for ctx in list(browser.contexts):
        for pg in list(ctx.pages):
            try:
                pg.close()
                closed += 1
            except Exception:
                pass
    return closed

def _close_others(browser: Browser, keep: Page) -> int:
    closed = 0
    for ctx in list(browser.contexts):
        for pg in list(ctx.pages):
            if pg is keep:
                continue
            try:
                pg.close()
                closed += 1
            except Exception:
                pass
    return closed

def _extract_value_near_label(page: Page, label_text: str, timeout_ms: int = 12000) -> str:
    """
    Find a node containing `label_text`, then search in its local card for a currency string.
    Avoids brittle class names; uses text + proximity.
    """
    # 1) Wait for the label to exist on the page
    label = page.get_by_text(label_text, exact=True).first
    label.wait_for(timeout=timeout_ms)

    # 2) Scroll into view (some overlays render off-screen initially)
    try:
        label.scroll_into_view_if_needed()
    except Exception:
        pass

    # 3) Use JS to climb up a few ancestors and find the first currency-looking text nearby
    val = page.evaluate(
        r"""
        (labelEl) => {
          const money = (t) => /^\$?\\s*\\d[\\d,]*(?:\\.\\d+)?$/.test((t||"").trim());

          function findCurrencyWithin(root) {
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
            while (walker.nextNode()) {
              const n = walker.currentNode;
              // Ignore the label node itself
              if (n === labelEl) continue;
              const txt = (n.innerText || "").trim();
              if (!txt) continue;
              // quick filter to skip obvious non-values
              if (txt.length > 40) continue;
              if (money(txt)) return txt;
            }
            return null;
          }

          // climb up to contain the card, then scan downward
          let root = labelEl.parentElement;
          for (let i = 0; i < 6 && root; i++) {
            const got = findCurrencyWithin(root);
            if (got) return got;
            root = root.parentElement;
          }
          // ultra fallback: scan whole doc (last resort)
          return findCurrencyWithin(document.body);
        }
        """,
        label.element_handle(),
    )

    if not val:
        raise RuntimeError(f"Could not find a currency value near '{label_text}'.")
    return val.strip()

def get_first_product_monthly_revenue(
    browser: Browser,
    *,
    product_search_url: str,
    ext_id: str = "",                 # kept for backward-compat, ignored now
    wait_secs: int = 30,
    popup_visible: bool = False,      # ignored
    close_all_tabs_first: bool = False,
    close_others_after_open: bool = True,
    close_seed_after_xray: bool = True,  # ignored, we close others right away
    label_text: str = "30-Day Revenue"
) -> Dict[str, str]:
    """
    NEW behavior:
      - (optionally) close all tabs up front
      - open product_search_url in a single visible tab
      - wait for the on-page overlay's "30-Day Revenue" card
      - extract the currency value next to that label
      - (optionally) close all other tabs so only this tab remains

    Returns: {"text": "$3,697,021.25", "number": "3697021.25"}
    """
    if close_all_tabs_first:
        n = _close_all_tabs(browser)
        if n:
            print(f"[info] Closed {n} tab(s) before starting.")

    ctx = _pick_ctx(browser)
    page = ctx.new_page()
    page.goto(product_search_url, wait_until="domcontentloaded")
    print("[info] Opened product page.")

    if close_others_after_open:
        n = _close_others(browser, keep=page)
        if n:
            print(f"[info] Closed {n} other tab(s); only the product tab remains.")

    # Give the overlay a moment if extension is still initializing
    deadline = time.time() + wait_secs
    last_err: Optional[Exception] = None
    value_text: Optional[str] = None

    while time.time() < deadline and value_text is None:
        try:
            value_text = _extract_value_near_label(page, label_text, timeout_ms=2500)
        except Exception as e:
            last_err = e
            time.sleep(0.35)

    if value_text is None:
        raise RuntimeError(
            f"'{label_text}' not found within {wait_secs}s. "
            f"Last error: {last_err}"
        )

    number = re.sub(r"[^0-9.]", "", value_text)
    print(f"[info] {label_text}: {value_text}")

    return {"text": value_text, "number": number}
