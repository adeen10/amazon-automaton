# profitcal.py
import re
import time
from typing import Dict, Optional
from playwright.sync_api import Browser, Page

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

def _clean_currency(s: str) -> str:
    return re.sub(r"[^0-9.]", "", (s or "").strip())

def _wait_for_all(page: Page, selectors: Dict[str, str], timeout_ms: int = 30000):
    for name, sel in selectors.items():
        try:
            page.wait_for_selector(sel, timeout=timeout_ms)
        except Exception:
            # Dump a small snippet for debug, but avoid massive page HTML
            try:
                snippet = page.inner_text("body", timeout=2000)
                snippet = (snippet[:1200] + "…") if len(snippet) > 1200 else snippet
            except Exception:
                snippet = "<body text unavailable>"
            raise RuntimeError(f"Missing selector for '{name}': {sel}\n\n[DEBUG SNIPPET]\n{snippet}")

def _click_calculator(page: Page, timeout_ms: int = 15000):
    """
    Clicks the Helium 'Profitability Calculator' button.
    Primary: data-testid="calculator"
    Fallbacks try role/text.
    """
    # Primary
    btn = page.locator('div[data-testid="calculator"]').first
    try:
        btn.wait_for(state="visible", timeout=timeout_ms)
        btn.click()
        print("[info] Clicked Helium Profitability Calculator button.")
        return
    except Exception:
        pass

    # Fallback by button role + text
    try:
        alt = page.get_by_role("button", name=re.compile(r"profitability|calculator", re.I)).first
        alt.wait_for(timeout=4000)
        alt.click()
        print("[info] Clicked Profitability Calculator (fallback).")
        return
    except Exception:
        pass

    # Last ditch: any element with calculator text
    try:
        any_calc = page.locator(":is(div,button,span,a):has-text('Calculator')").first
        any_calc.wait_for(state="visible", timeout=4000)
        any_calc.click()
        print("[info] Clicked Calculator (text fallback).")
        return
    except Exception:
        pass

    raise RuntimeError("Could not find/click the Profitability Calculator button.")

def _get_fba_fees(page: Page) -> str:
    """
    FBA fees are sometimes rendered with volatile classes.
    Try your original class selector, then fall back to a proximity search
    around 'FBA Fees'.
    """
    # Original class-based selector (brittle but fast if it works)
    try:
        el = page.locator("div.sc-gsnOKb.jESxTP").first
        el.wait_for(timeout=2000)
        txt = (el.inner_text() or "").strip()
        if txt:
            return txt
    except Exception:
        pass

    # Proximity fallback near 'FBA Fees'
    try:
        label = page.get_by_text("FBA Fees", exact=False).first
        label.wait_for(timeout=3000)
        # climb ancestors and scan for a currency-looking piece of text
        val = page.evaluate(
            """
            (labelEl) => {
              const money = (t) => /^\\$?\\s*\\d[\\d,]*(?:\\.\\d+)?$/.test((t||"").trim());
              function findCurrencyWithin(root) {
                const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
                while (walker.nextNode()) {
                  const n = walker.currentNode;
                  if (n === labelEl) continue;
                  const txt = (n.innerText || "").trim();
                  if (!txt || txt.length > 40) continue;
                  if (money(txt)) return txt;
                }
                return null;
              }
              let root = labelEl.parentElement;
              for (let i = 0; i < 6 && root; i++) {
                const got = findCurrencyWithin(root);
                if (got) return got;
                root = root.parentElement;
              }
              return null;
            }
            """,
            label.element_handle(),
        )
        if val:
            return val.strip()
    except Exception:
        pass

    raise RuntimeError("Could not read FBA Fees from the calculator panel.")

def get_profitability_metrics(
    browser: Browser,
    *,
    product_url: str,
    wait_secs: int = 60,
    close_all_tabs_first: bool = False,
    close_others_after_open: bool = True,
) -> Dict[str, Dict[str, str]]:
    """
    Navigate to product_url, open Helium Profitability Calculator, and return:
      {
        "fba_fees": {"text": "$X.XX", "number": "X.XX"},
        "storage_fee_jan_sep": {"text": "$X.XX", "number": "X.XX"},
        "storage_fee_oct_dec": {"text": "$X.XX", "number": "X.XX"},
        "product_price": {"text": "123.45", "number": "123.45"}
      }
    """
    if close_all_tabs_first:
        n = _close_all_tabs(browser)
        if n:
            print(f"[info] Closed {n} tab(s) before starting.")

    ctx = _pick_ctx(browser)
    page = ctx.new_page()
    page.goto(product_url, wait_until="domcontentloaded")
    page.bring_to_front()
    print("[info] Opened Amazon product page (seed).")

    if close_others_after_open:
        n = _close_others(browser, keep=page)
        if n:
            print(f"[info] Closed {n} other tab(s); only the product tab remains.")

    # Open calculator
    _click_calculator(page, timeout_ms=15000)

    # Wait for critical calculator fields
    selectors = {
        "storage_fee_jan_sep": 'div[data-testid="calculator-profitability-storageFeeJanSep"]',
        "storage_fee_oct_dec": 'div[data-testid="calculator-profitability-storageFeeOctDec"]',
        "product_price": 'input[data-testid="calculator-profitability-price"]',
    }

    deadline = time.time() + wait_secs
    last_err: Optional[Exception] = None
    while time.time() < deadline:
        try:
            _wait_for_all(page, selectors, timeout_ms=2500)
            break
        except Exception as e:
            last_err = e
            time.sleep(0.3)
    else:
        raise RuntimeError(f"Profitability Calculator UI did not appear in {wait_secs}s. Last error: {last_err}")

    # Extract values
    storage_fee_jan_sep_text = (page.locator(selectors["storage_fee_jan_sep"]).inner_text() or "").strip()
    storage_fee_oct_dec_text = (page.locator(selectors["storage_fee_oct_dec"]).inner_text() or "").strip()
    product_price_text = (page.locator(selectors["product_price"]).input_value() or "").strip()
    fba_fees_text = _get_fba_fees(page)

    result = {
        "fba_fees": {
            "text": fba_fees_text,
            "number": _clean_currency(fba_fees_text),
        },
        "storage_fee_jan_sep": {
            "text": storage_fee_jan_sep_text,
            "number": _clean_currency(storage_fee_jan_sep_text),
        },
        "storage_fee_oct_dec": {
            "text": storage_fee_oct_dec_text,
            "number": _clean_currency(storage_fee_oct_dec_text),
        },
        "product_price": {
            "text": product_price_text,
            "number": _clean_currency(product_price_text),
        },
    }

    print("[info] Profitability metrics captured.")
    return result
