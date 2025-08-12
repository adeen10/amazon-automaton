# from playwright.sync_api import sync_playwright
# from datetime import datetime, timezone, timedelta
# from csv_picker import find_top_recent_product
# import os,re, time

# CDP_URL = "http://127.0.0.1:9666"

# def clean(s):
#     import re
#     return re.sub(r"\s+", " ", s or "").strip()

# with sync_playwright() as p:
#     browser = p.chromium.connect_over_cdp(CDP_URL)

#     # 1) find the Amazon tab that has XRAY visible
#     page = None
#     for ctx in browser.contexts:
#         for pg in ctx.pages:
#             if "amazon." not in pg.url:
#                 continue
#             try:
#                 pg.get_by_text("Xray", exact=False).first.wait_for(timeout=1200)
#                 page = pg
#                 break
#             except:
#                 pass
#         if page:
#             break
#     if not page:
#         raise RuntimeError("XRAY not detected on any Amazon tab.")

#     page.bring_to_front()
#     page.wait_for_timeout(400)

#     # 2) open Filters
#     filters_btn = page.get_by_role("button", name=re.compile(r"^\s*Filters\s*$", re.I))
#     try:
#         filters_btn.wait_for(timeout=5000)
#         try:
#             filters_btn.click(timeout=1500)
#             print("[INFO] Filters clicked (normal).")
#         except:
#             # fallback: programmatic click (bypasses overlay intercepts)
#             el = filters_btn.element_handle()
#             if el:
#                 page.evaluate("(el)=>el.click()", el)
#                 print("[INFO] Filters clicked (programmatic).")
#     except Exception as e:
#         # broader fallback by text
#         alt = page.locator("button:has-text('Filters')").first
#         alt.wait_for(timeout=3000)
#         page.evaluate("(el)=>el.click()", alt.element_handle())
#         print("[INFO] Filters clicked (alt).")

#     # 3) wait for the filter panel to appear; scope inside it
#     page.locator("input[placeholder='Max'][type='number']").first.wait_for(timeout=10000)

#     # helper: get the Nth *visible* match of a locator (0-based)
#     def nth_visible(loc, n, timeout_ms=10000):
#         end = time.time() + (timeout_ms / 1000.0)
#         idx = -1
#         while time.time() < end:
#             count = loc.count()
#             vis = []
#             # collect visibility status in current snapshot
#             for i in range(count):
#                 el = loc.nth(i)
#                 try:
#                     if el.is_visible():
#                         vis.append(i)
#                 except:
#                     pass
#             if len(vis) > n:
#                 return loc.nth(vis[n])
#             time.sleep(0.2)
#         raise RuntimeError(f"Only found {len(vis)} visible 'Max' inputs; need index {n} (8th).")

#     # pick the 8th visible 'Max' input (index 7)
#     target_max = nth_visible(page.locator("input[placeholder='Max'][type='number']"), 7)
#     target_max.scroll_into_view_if_needed()

#     # set value = 1000 (robust: try normal fill/type; fallback to JS)
#     try:
#         target_max.fill("")
#         target_max.type("1000", delay=25)
#     except:
#         el = target_max.element_handle()
#         page.evaluate("(el)=>{ el.value='1000'; el.dispatchEvent(new Event('input', {bubbles:true})); }", el)

#     print("[INFO] Set 8th 'Max' input = 1000")
    
#     # 3(b)
#     # --- Title Keyword Search = "cricket bat" (4th visible "Select one or more") ---
#     # ensure those inputs exist
#     # --- Title Keyword Search = "cricket bat" (expand section then fill) ---
#     # 1) find the section by its label
#     title_section = page.locator("div.sc-lkIYrd:has-text('Title Keyword Search')").first
#     title_section.wait_for(timeout=8000)

#     # 2) if it's collapsed, expand it
#     try:
#         expanded = title_section.locator("[aria-expanded]").first
#         state = expanded.get_attribute("aria-expanded")
#         if state == "false":
#             # click on the label area to expand; fallback to programmatic click
#             try:
#                 title_section.get_by_text("Title Keyword Search", exact=False).first.click(timeout=1500)
#             except:
#                 el = title_section.get_by_text("Title Keyword Search", exact=False).first.element_handle()
#                 if el:
#                     page.evaluate("(el)=>el.click()", el)
#             # give it a moment to render
#             page.wait_for_timeout(400)
#     except:
#         pass  # some builds may not expose aria-expanded

#     # 3) locate the input inside this section
#     #    Helium uses a real <input> here in your HTML
#     title_input = title_section.locator("input[placeholder='Select one or more']").first
#     title_input.scroll_into_view_if_needed()

#     # 4) type the keyword (fallback to programmatic set + Enter)
#     typed = False
#     try:
#         title_input.click(timeout=1500)
#         title_input.fill("")
#         title_input.type("candy", delay=20)
#         page.keyboard.press("Enter")
#         typed = True
#         print("[INFO] Title Keyword Search set via typing.")
#     except:
#         pass

#     if not typed:
#         el = title_input.element_handle()
#         page.evaluate(
#             """(el) => {
#                 el.value = 'cricket bat';
#                 el.dispatchEvent(new Event('input', { bubbles: true }));
#             }""",
#             el
#         )
#         try:
#             title_input.focus()
#         except:
#             pass
#         page.keyboard.press("Enter")
#         print("[INFO] Title Keyword Search set programmatically.")

    
    
#     # 4) click Apply Filters
#     apply_btn = page.get_by_role("button", name=re.compile(r"^\s*Apply Filters\s*$", re.I))
#     try:
#         apply_btn.wait_for(timeout=5000)
#         try:
#             apply_btn.click(timeout=1500)
#             print("[INFO] Apply Filters clicked (normal).")
#         except:
#             el = apply_btn.element_handle()
#             page.evaluate("(el)=>el.click()", el)
#             print("[INFO] Apply Filters clicked (programmatic).")
#     except Exception as e:
#         # last-ditch: any button with text
#         alt_apply = page.locator("button:has-text('Apply Filters')").first
#         alt_apply.wait_for(timeout=3000)
#         page.evaluate("(el)=>el.click()", alt_apply.element_handle())
#         print("[INFO] Apply Filters clicked (alt).")

#     # 5) give XRAY time to recompute
#     print("[INFO] Waiting for results to refresh…")
#     page.wait_for_timeout(8000)
    
    
    
    

#     # --- EXPORT → CSV robust flow ---
#     # --- EXPORT → CSV (class-based selectors using your HTML) ---
#     DOWNLOAD_DIR = r"E:\automation\exports"
#     os.makedirs(DOWNLOAD_DIR, exist_ok=True)

#     # 1) Open Export (you already do this)
#     export_btn = page.get_by_role("button", name=re.compile(r"\bExport\b", re.I))
#     try:
#         export_btn.click(timeout=2000)
#     except:
#         page.locator("button:has-text('Export'), .sc-eoEtVK:has-text('Export')").first.evaluate("el=>el.click()")
#     print("[info] Export menu opened.")

#     # 2) Wait for the tile container that holds CSV/XLSX options
#     #    Based on your snippet:  .sc-eWhHU  contains two .sc-brSOsn tiles
#     menu_root = page.locator("div.sc-eWhHU").filter(has=page.locator("div.sc-brSOsn")).first
#     try:
#         menu_root.wait_for(timeout=5000)
#     except:
#         # Fallback: try to locate any visible CSV tile globally
#         menu_root = None
#         print("[warn] .sc-eWhHU not visible; will search CSV tile globally.")

#     # 3) Resolve the CSV tile
#     csv_tile = None
#     try:
#         if menu_root:
#             csv_tile = menu_root.locator("div.sc-brSOsn", has_text=re.compile(r"CSV", re.I)).first
#             csv_tile.wait_for(state="visible", timeout=2000)
#         else:
#             csv_tile = page.locator("div.sc-brSOsn", has_text=re.compile(r"CSV", re.I)).first
#             csv_tile.wait_for(state="visible", timeout=3000)
#     except:
#         # Ultra-fallback: any element with that text
#         csv_tile = page.locator(":is(div,button,span,a):has-text('as a CSV file'), :is(div,button,span,a):has-text('CSV')").first
#         csv_tile.wait_for(state="visible", timeout=3000)
        
#     downloaded_path = None

#     # 4) Try native download first
#     downloaded = False
#     try:
#         with page.expect_download(timeout=15000) as dl_info:
#             try:
#                 csv_tile.scroll_into_view_if_needed()
#             except:
#                 pass
#             try:
#                 csv_tile.click(timeout=1500, force=True)
#             except:
#                 page.evaluate("(el)=>el.click()", csv_tile.element_handle())
#         download = dl_info.value
#         suggested = download.suggested_filename or "xray_export.csv"
#         stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         base, ext = os.path.splitext(suggested)
#         save_as = os.path.join(DOWNLOAD_DIR, f"{base}_{stamp}{ext}")
#         download.save_as(save_as)
#         print(f"[success] Downloaded CSV to: {save_as}")
#         downloaded_path = save_as
#         downloaded = True
#     except Exception as e:
#         print("[warn] Native download event not seen, trying response-sniff method…", e)

#     # 5) If no native download, catch the CSV response and save it
#     if not downloaded:
#         # Click again (in case the previous click was swallowed)
#         try:
#             csv_tile.click(timeout=1500, force=True)
#         except:
#             try:
#                 page.evaluate("(el)=>el.click()", csv_tile.element_handle())
#             except:
#                 pass

#         def _looks_like_csv(resp):
#             if not resp.ok:
#                 return False
#             ctype = (resp.headers.get("content-type", "") or "").lower()
#             dispo = (resp.headers.get("content-disposition", "") or "").lower()
#             return ("text/csv" in ctype) or ("attachment" in dispo and "csv" in dispo)

#         resp = page.wait_for_event("response", timeout=20000, predicate=_looks_like_csv)
#         body = resp.body()

#         # filename from headers if present
#         fname = "xray_export_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
#         m = re.search(r'filename="?([^";]+)"?', resp.headers.get("content-disposition", "") or "")
#         if m:
#             fname = m.group(1)
#             # ensure .csv extension
#             if not fname.lower().endswith(".csv"):
#                 fname += ".csv"

#         path = os.path.join(DOWNLOAD_DIR, fname)
#         with open(path, "wb") as f:
#             f.write(body)
#         print(f"[success] Saved CSV via response sniffing: {path}")
#         downloaded_path = path
        
        
#     # --- Now call your CSV picker dynamically ---
#     if downloaded_path:
#         best = find_top_recent_product(downloaded_path, within_years=2)
#         if not best:
#             print("No qualifying product found.")
#         else:
#             print("Top recent product:", best["product_details"])
#             print("URL:", best["url"])
#             print("Parent Revenue:", best["parent_level_revenue"])
#             print("Creation Date:", best["creation_date"])
#     else:
#         print("[ERROR] No CSV file was downloaded.")


    

#     # 6) (optional) read updated Total Revenue again
#     try:
#         label = page.get_by_text("Total Revenue", exact=True).first
#         label.wait_for(timeout=5000)
#         el = label.element_handle()
#         value_text = page.evaluate(
#             """
#             (labelEl) => {
#               function findValueWithin(root) {
#                 const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
#                 while (walker.nextNode()) {
#                   const n = walker.currentNode;
#                   const txt = (n.innerText || "").trim();
#                   if (!txt) continue;
#                   if (/^\\$?\\s*\\d[\\d,]*(?:\\.\\d+)?$/.test(txt) && !/total\\s*revenue/i.test(txt)) {
#                     return txt;
#                   }
#                 }
#                 return null;
#               }
#               let root = labelEl.parentElement;
#               for (let i = 0; i < 5 && root; i++) {
#                 const val = findValueWithin(root);
#                 if (val) return val;
#                 root = root.parentElement;
#               }
#               return null;
#             }
#             """,
#             el
#         )
#         if value_text:
#             value_text = clean(value_text)
#             number_only = re.sub(r"[^0-9.]", "", value_text)
#             print("Total Revenue:", value_text)
#             print("Total Revenue (number):", number_only)
#         else:
#             print("[WARN] Couldn’t find updated Total Revenue.")
#     except Exception as e:
#         print("[WARN] Total Revenue read failed:", e)

#     input("Press Enter to disconnect…")


# competitors.py
import os, re, time
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

from playwright.sync_api import Browser, Page
from csv_picker import find_top_recent_product


# ---------- helpers ----------
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

def _nth_visible(loc, n: int, timeout_ms: int = 10000):
    """Return the nth (0-based) *visible* element of a locator."""
    end = time.time() + (timeout_ms / 1000.0)
    last_vis = []
    while time.time() < end:
        try:
            count = loc.count()
        except Exception:
            time.sleep(0.2); continue

        vis = []
        for i in range(count):
            el = loc.nth(i)
            try:
                if el.is_visible():
                    vis.append(i)
            except Exception:
                pass

        last_vis = vis
        if len(vis) > n:
            return loc.nth(vis[n])
        time.sleep(0.2)

    raise RuntimeError(f"Only found {len(last_vis)} visible matches; need index {n}.")

def _click_like_a_human_then_programmatic(page: Page, loc) -> bool:
    """Try normal click, then JS click if needed. Return True if clicked."""
    try:
        loc.scroll_into_view_if_needed()
    except Exception:
        pass
    try:
        loc.click(timeout=1500)
        return True
    except Exception:
        try:
            el = loc.element_handle()
            if el:
                page.evaluate("(el)=>el.click()", el)
                return True
        except Exception:
            return False
    return False

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
    value_text = re.sub(r"\s+", " ", value_text).strip()
    number_only = re.sub(r"[^0-9.]", "", value_text)
    return value_text, number_only


# ---------- main function ----------
def run_competitors_flow(
    browser: Browser,
    *,
    download_dir: str = r"E:\automation\exports",
    max_input_visible_index: int = 7,   # 8th visible "Max" input
    max_value: str = "1000",
    title_keyword: str = "candy",
    wait_after_apply_ms: int = 8000,
    picker_within_years: int = 2,
    try_read_updated_revenue: bool = True
) -> Dict[str, Any]:
    """
    Uses an existing Playwright Browser to:
      1) find the XRAY page
      2) open Filters
      3) set the Nth visible 'Max' input to max_value
      4) set Title Keyword Search to `title_keyword`
      5) Apply Filters and wait
      6) Export -> CSV (native download or response-sniff fallback)
      7) Run csv_picker.find_top_recent_product on the CSV
      8) (optional) read updated 'Total Revenue' again

    Returns a dict with keys:
      {
        "downloaded_path": <str | None>,
        "picker_best": <dict | None>,
        "updated_total_revenue_text": <str | None>,
        "updated_total_revenue_number": <str | None>
      }
    """
    # 1) locate XRAY page
    page = _find_xray_page(browser, timeout_ms=1200)
    if not page:
        raise RuntimeError("XRAY not detected on any Amazon tab.")
    page.bring_to_front()
    page.wait_for_timeout(400)

    # 2) open Filters
    filters_btn = page.get_by_role("button", name=re.compile(r"^\s*Filters\s*$", re.I))
    try:
        filters_btn.wait_for(timeout=5000)
        if _click_like_a_human_then_programmatic(page, filters_btn):
            print("[INFO] Filters clicked.")
        else:
            raise Exception("Primary click failed")
    except Exception:
        alt = page.locator("button:has-text('Filters')").first
        alt.wait_for(timeout=3000)
        page.evaluate("(el)=>el.click()", alt.element_handle())
        print("[INFO] Filters clicked (alt).")

    # 3) wait for filter panel to appear
    max_inputs = page.locator("input[placeholder='Max'][type='number']")
    max_inputs.first.wait_for(timeout=10000)

    # pick the Nth visible 'Max' input and set value
    target_max = _nth_visible(max_inputs, max_input_visible_index)
    target_max.scroll_into_view_if_needed()
    try:
        target_max.fill("")
        target_max.type(max_value, delay=25)
    except Exception:
        el = target_max.element_handle()
        if el:
            page.evaluate(
                "(el, val)=>{ el.value=val; el.dispatchEvent(new Event('input',{bubbles:true})); }",
                el, max_value
            )
    print(f"[INFO] Set {max_input_visible_index+1}th 'Max' input = {max_value}")

    # 3b) Title Keyword Search section -> set keyword
    title_section = page.locator("div.sc-lkIYrd:has-text('Title Keyword Search')").first
    title_section.wait_for(timeout=8000)

    try:
        expanded = title_section.locator("[aria-expanded]").first
        state = expanded.get_attribute("aria-expanded")
        if state == "false":
            try:
                title_section.get_by_text("Title Keyword Search", exact=False).first.click(timeout=1500)
            except Exception:
                el = title_section.get_by_text("Title Keyword Search", exact=False).first.element_handle()
                if el:
                    page.evaluate("(el)=>el.click()", el)
            page.wait_for_timeout(400)
    except Exception:
        pass

    title_input = title_section.locator("input[placeholder='Select one or more']").first
    title_input.scroll_into_view_if_needed()

    typed = False
    try:
        title_input.click(timeout=1500)
        title_input.fill("")
        title_input.type(title_keyword, delay=20)
        page.keyboard.press("Enter")
        typed = True
        print(f"[INFO] Title Keyword Search set via typing: {title_keyword}")
    except Exception:
        pass

    if not typed:
        el = title_input.element_handle()
        page.evaluate(
            """(el, val) => {
                el.value = val;
                el.dispatchEvent(new Event('input', { bubbles: true }));
            }""",
            el, title_keyword
        )
        try:
            title_input.focus()
        except Exception:
            pass
        page.keyboard.press("Enter")
        print(f"[INFO] Title Keyword Search set programmatically: {title_keyword}")

    # 4) Apply Filters
    apply_btn = page.get_by_role("button", name=re.compile(r"^\s*Apply Filters\s*$", re.I))
    try:
        apply_btn.wait_for(timeout=5000)
        if _click_like_a_human_then_programmatic(page, apply_btn):
            print("[INFO] Apply Filters clicked.")
        else:
            raise Exception("Primary click failed")
    except Exception:
        alt_apply = page.locator("button:has-text('Apply Filters')").first
        alt_apply.wait_for(timeout=3000)
        page.evaluate("(el)=>el.click()", alt_apply.element_handle())
        print("[INFO] Apply Filters clicked (alt).")

    print("[INFO] Waiting for results to refresh…")
    page.wait_for_timeout(wait_after_apply_ms)

    # 5) EXPORT -> CSV
    os.makedirs(download_dir, exist_ok=True)
    export_btn = page.get_by_role("button", name=re.compile(r"\bExport\b", re.I))
    try:
        export_btn.click(timeout=2000)
    except Exception:
        page.locator("button:has-text('Export'), .sc-eoEtVK:has-text('Export')").first.evaluate("el=>el.click()")
    print("[INFO] Export menu opened.")

    menu_root = page.locator("div.sc-eWhHU").filter(has=page.locator("div.sc-brSOsn")).first
    try:
        menu_root.wait_for(timeout=5000)
    except Exception:
        menu_root = None
        print("[WARN] .sc-eWhHU not visible; searching CSV tile globally.")

    csv_tile = None
    try:
        if menu_root:
            csv_tile = menu_root.locator("div.sc-brSOsn", has_text=re.compile(r"CSV", re.I)).first
            csv_tile.wait_for(state="visible", timeout=2000)
        else:
            csv_tile = page.locator("div.sc-brSOsn", has_text=re.compile(r"CSV", re.I)).first
            csv_tile.wait_for(state="visible", timeout=3000)
    except Exception:
        csv_tile = page.locator(
            ":is(div,button,span,a):has-text('as a CSV file'), :is(div,button,span,a):has-text('CSV')"
        ).first
        csv_tile.wait_for(state="visible", timeout=3000)

    downloaded_path = None
    downloaded = False
    try:
        with page.expect_download(timeout=15000) as dl_info:
            try:
                csv_tile.scroll_into_view_if_needed()
            except Exception:
                pass
            if not _click_like_a_human_then_programmatic(page, csv_tile):
                raise Exception("CSV tile click failed")
        download = dl_info.value
        suggested = download.suggested_filename or "xray_export.csv"
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(suggested)
        save_as = os.path.join(download_dir, f"{base}_{stamp}{ext or '.csv'}")
        download.save_as(save_as)
        print(f"[success] Downloaded CSV to: {save_as}")
        downloaded_path = save_as
        downloaded = True
    except Exception as e:
        print("[WARN] Native download event not seen, trying response-sniff method…", e)

    if not downloaded:
        # try again and sniff response
        try:
            _click_like_a_human_then_programmatic(page, csv_tile)
        except Exception:
            pass

        def _looks_like_csv(resp):
            try:
                if not resp.ok:
                    return False
                ctype = (resp.headers.get("content-type", "") or "").lower()
                dispo = (resp.headers.get("content-disposition", "") or "").lower()
                return ("text/csv" in ctype) or ("attachment" in dispo and "csv" in dispo)
            except Exception:
                return False

        resp = page.wait_for_event("response", timeout=20000, predicate=_looks_like_csv)
        body = resp.body()

        fname = "xray_export_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
        m = re.search(r'filename="?([^";]+)"?', resp.headers.get("content-disposition", "") or "")
        if m:
            fname = m.group(1)
            if not fname.lower().endswith(".csv"):
                fname += ".csv"

        downloaded_path = os.path.join(download_dir, fname)
        with open(downloaded_path, "wb") as f:
            f.write(body)
        print(f"[success] Saved CSV via response sniffing: {downloaded_path}")

    # 6) Pick best product from CSV
    picker_best = None
    if downloaded_path:
        picker_best = find_top_recent_product(downloaded_path, within_years=picker_within_years)
        if not picker_best:
            print("[INFO] No qualifying product found in CSV.")
        else:
            print("[INFO] Top recent product:", picker_best.get("product_details"))
            print("       URL:", picker_best.get("url"))
            print("       Parent Revenue:", picker_best.get("parent_level_revenue"))
            print("       Creation Date:", picker_best.get("creation_date"))
    else:
        print("[ERROR] No CSV file was downloaded.")

    # 7) (optional) read updated Total Revenue again
    updated_text = None
    updated_num = None
    if try_read_updated_revenue:
        try:
            updated_text, updated_num = _extract_total_revenue(page)
            print(f"[INFO] Updated Total Revenue: {updated_text} | number: {updated_num}")
        except Exception as e:
            print("[WARN] Total Revenue read failed:", e)

    return {
        "downloaded_path": downloaded_path,
        "picker_best": picker_best,
        "updated_total_revenue_text": updated_text,
        "updated_total_revenue_number": updated_num,
    }
