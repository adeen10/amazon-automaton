# get_category_rev.py
import re, time
from typing import Optional, Tuple, Dict
from playwright.sync_api import Browser, Page

def _clean(s: Optional[str]) -> str:
    import re
    return re.sub(r"\s+", " ", s or "").strip()

def _find_xray_page(browser: Browser, timeout_ms: int = 1500) -> Optional[Page]:
    """Return the Amazon tab that actually has the XRAY overlay text visible."""
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if "amazon." not in pg.url:
                continue
            try:
                pg.get_by_text("Xray", exact=False).first.wait_for(timeout=timeout_ms)
                return pg
            except Exception:
                pass
    return None

def _click_load_more(page: Page) -> bool:
    """Try multiple strategies to click 'Load More'. Return True if clicked."""
    clicked = False
    load_more = page.get_by_role("button", name=re.compile(r"^\s*Load More\s*$", re.I))
    try:
        load_more.wait_for(timeout=4000)
        load_more.scroll_into_view_if_needed()
        try:
            load_more.click(timeout=1500)
            print("[INFO] Load More clicked (normal).")
            return True
        except Exception:
            el = load_more.element_handle()
            if el:
                page.evaluate("(el)=>el.click()", el)
                print("[INFO] Load More clicked (programmatic).")
                return True
    except Exception:
        # fallback selector
        try:
            load_more = page.locator("button:has-text('Load More')").first
            load_more.scroll_into_view_if_needed()
            el = load_more.element_handle()
            if el:
                page.evaluate("(el)=>el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}))", el)
                print("[INFO] Load More clicked (dispatchEvent fallback).")
                return True
        except Exception:
            pass
    return clicked

def _extract_total_revenue(page: Page) -> Tuple[str, str]:
    """Find the 'Total Revenue' label and extract the nearest numeric value."""
    label = page.get_by_text("Total Revenue", exact=True).first
    label.wait_for(timeout=5000)
    el = label.element_handle()
    if not el:
        raise RuntimeError("Couldn't get handle for 'Total Revenue' label.")

    value_text = page.evaluate(
        """
        (labelEl) => {
          function findValueWithin(root) {
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
            while (walker.nextNode()) {
              const n = walker.currentNode;
              const txt = (n.innerText || "").trim();
              if (!txt) continue;
              if (/^\\$?\\s*\\d[\\d,]*(?:\\.\\d+)?$/.test(txt) && !/total\\s*revenue/i.test(txt)) {
                return txt;
              }
            }
            return null;
          }
          let root = labelEl.parentElement;
          for (let i = 0; i < 5 && root; i++) {
            const val = findValueWithin(root);
            if (val) return val;
            root = root.parentElement;
          }
          return null;
        }
        """,
        el
    )
    if not value_text:
        raise RuntimeError("Couldn't locate the Total Revenue value near the label.")
    value_text = _clean(value_text)
    number_only = re.sub(r"[^0-9.]", "", value_text)
    return value_text, number_only

def get_category_revenue(browser: Browser, *, wait_after_click_ms: int = 15000) -> Dict[str, str]:
    """
    Uses an existing Playwright Browser to:
      - find the XRAY page
      - click 'Load More' (best effort)
      - read 'Total Revenue' (both text and numeric)
    Returns: {'text': <e.g. '$123,456'>, 'number': <e.g. '123456'>}
    """
    page = _find_xray_page(browser, timeout_ms=1200)
    if not page:
        raise RuntimeError("XRAY not detected on any Amazon tab.")
    page.bring_to_front()
    page.wait_for_timeout(500)

    if _click_load_more(page):
        print("[INFO] Waiting 15s for data to refresh…")
        page.wait_for_timeout(wait_after_click_ms)
    else:
        print("[WARN] Could not click 'Load More' (overlay likely intercepting). Continuing anyway.")

    value_text, number_only = _extract_total_revenue(page)
    print(f"[RESULT] Total Revenue: {value_text}  |  number: {number_only}")
    return {"text": value_text, "number": number_only}


