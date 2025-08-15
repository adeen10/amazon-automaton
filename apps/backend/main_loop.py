# Launch.py
import os, re, time, json
from typing import Dict, Any, List, Tuple
from playwright.sync_api import Browser
from helium_boot import boot_and_xray
from getCategoryRev import get_category_revenue
from competitors import run_competitors_flow
from monthlyrev import run_monthlyrev
from profitcal import get_profitability_metrics
from cerebro import open_amazon_page, open_cerebro_from_xray, cerebro_search, export_cerebro_csv
from gpt import get_keywords_volumes_from_csv, get_gpt_response
from sheet_writer import write_results_to_country_tabs
# ---------------------------
# ENV / CONSTANTS
# ---------------------------
# USERNAME = "Al-Wajid Laptops"
USERNAME = "Hurai"
# CHROME_PATH   = rf"C:\Users\{USERNAME}\AppData\Local\Google\Chrome\Application\chrome.exe"
CHROME_PATH   = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = rf"C:\Users\{USERNAME}\automation-profile"
PROFILE_DIR   = "Profile 4"
EXT_ID        = "njmehopjdpcckochcggncklnlmikcbnb"

BASE_EXPORT_DIR            = os.path.join(os.getcwd(), "exports")
CEREBRO_DOWNLOAD_DIR       = os.path.join(BASE_EXPORT_DIR, "cerebro")
COMPETITORS_DOWNLOAD_DIR   = BASE_EXPORT_DIR
MONTHLY_REV_DOWNLOAD_DIR   = os.path.join(BASE_EXPORT_DIR, "monthlyrev")
for d in [CEREBRO_DOWNLOAD_DIR, COMPETITORS_DOWNLOAD_DIR, MONTHLY_REV_DOWNLOAD_DIR]:
    os.makedirs(d, exist_ok=True)

MAX_RETRIES = 5

# ---------------------------
# XRAY opener (unchanged)
# ---------------------------
def open_with_xray(
    browser: Browser,
    *,
    ext_id: str,
    target_url: str,
    wait_secs: int = 20,
    popup_visible: bool = False
):
    """
    Reuse existing Playwright Browser to tell Helium to open target_url with XRAY.
    Does NOT call sync_playwright().start() again.
    """
    if not browser.contexts:
        ctx = browser.new_context()
    else:
        ctx = browser.contexts[0]
    
    popup_url = f"chrome-extension://{ext_id}/popup.html"
    popup = ctx.new_page()
    popup.goto(popup_url, wait_until="domcontentloaded")

    popup.evaluate(
        """(targetUrl) => new Promise((resolve) => {
            chrome.runtime.sendMessage(
                { type: "open-page-and-xray", params: { url: targetUrl } },
                () => resolve(true)
            );
            setTimeout(() => resolve(false), 30000);
        })""",
        target_url,
    )
    print(f"[info] Sent XRAY open-page for {target_url}")
    if not popup_visible:
        try: popup.close()
        except Exception: pass

    # Optional: light wait loop so navigation starts before next step
    deadline = time.time() + wait_secs
    while time.time() < deadline:
        for pg in ctx.pages:
            if "amazon." in pg.url:
                try:
                    pg.get_by_role("button", name=re.compile(r"\bExport\b", re.I)).first.wait_for(timeout=300)
                    print("[SUCCESS] XRAY export UI detected.")
                    return pg
                except Exception:
                    pass
        time.sleep(0.25)
    print("[warn] Did not positively detect XRAY within wait; proceeding anyway.")
    return None

# ---------------------------
# Per-product run
# ---------------------------
def run_single_product(
    *,
    category_url: str,
    product_url: str,
    keyword: str
) -> Dict[str, Any]:
    """
    Boot Chrome+XRAY, run full pipeline for one product, return structured results.
    """
    print("\n" + "="*80)
    print(f"[RUN] category_url={category_url}\n      product_url={product_url}\n      keyword={keyword}")
    print("="*80)

    # Boot & land on category (ensures Helium is initialized for the marketplace)
    pw, browser, ctx, _ = boot_and_xray(
        chrome_path=CHROME_PATH,
        user_data_dir=USER_DATA_DIR,
        profile_dir=PROFILE_DIR,
        ext_id=EXT_ID,
        target_url=category_url,
        cdp_port=9666,
        wait_secs=20
    )
    print("[ok] boot complete; XRAY should be running.")

    # Initialize results container
    run_results: Dict[str, Any] = {
        "inputs": {
            "category_url": category_url,
            "product_url": product_url,
            "keyword": keyword
        },
        "category_revenue": {"text": None, "number": None},
        "monthly_revenue": {"meta": None},
        "competitors_flow": {"picker_best": None, "raw_result": None},
        "profitability_metrics": {
            "fba_fees": {"text": None, "number": None},
            "storage_fee_jan_sep": {"text": None, "number": None},
            "storage_fee_oct_dec": {"text": None, "number": None},
            "product_price": {"text": None, "number": None}
        },
        "keywords_volumes": {"user_prompt": None, "search_volumes": None},
        "gpt_projection": {"response": None},
        "errors": []
    }

    # ---- Category revenue (retry) ----
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print("[Info] Getting Category Revenue")
            rev = get_category_revenue(browser, wait_after_click_ms=15000)
            run_results["category_revenue"]["text"]   = rev.get("text")
            run_results["category_revenue"]["number"] = rev.get("number")
            break
        except Exception as e:
            msg = f"category_revenue attempt {attempt} failed: {e}"
            print("[ERROR]", msg)
            run_results["errors"].append(msg)
            if "xray not detected" in str(e).lower():
                print("[WARN] XRAY not detected, rebooting browser...")
                try:
                    [p.close() for p in ctx.pages]
                except Exception:
                    pass
                browser.close(); pw.stop()
                pw, browser, ctx, _ = boot_and_xray(
                    chrome_path=CHROME_PATH,
                    user_data_dir=USER_DATA_DIR,
                    profile_dir=PROFILE_DIR,
                    ext_id=EXT_ID,
                    target_url=category_url,
                    cdp_port=9666,
                    wait_secs=20
                )
            if attempt == MAX_RETRIES:
                print("[ERROR] Category revenue: max retries reached.")

    # ---- Monthly revenue for THIS product ----
    try:
        print("[Info] Opening product for monthly revenue + profit calc.")
        open_with_xray(browser, ext_id=EXT_ID, target_url=product_url, wait_secs=20, popup_visible=False)
    except Exception as e:
        msg = f"open_with_xray(product) failed: {e}"
        print("[ERROR]", msg)
        run_results["errors"].append(msg)

    try:
        print("[Info] Getting Monthly Revenue CSV.")
        meta = run_monthlyrev(browser, download_dir=MONTHLY_REV_DOWNLOAD_DIR)
        run_results["monthly_revenue"]["meta"] = meta
    except Exception as e:
        msg = f"run_monthlyrev failed: {e}"
        print("[ERROR]", msg)
        run_results["errors"].append(msg)
    finally:
        # cleanup monthlyrev CSVs
        for file in os.listdir(MONTHLY_REV_DOWNLOAD_DIR):
            if file.endswith(".csv"):
                try: os.remove(os.path.join(MONTHLY_REV_DOWNLOAD_DIR, file))
                except Exception: pass

    # ---- Competitors flow (retry) ----
    COMPETITOR_PRODUCT_URL = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print("[Info] Running Competitors flow.")
            result = run_competitors_flow(
                browser,
                download_dir=COMPETITORS_DOWNLOAD_DIR,
                max_input_visible_index=7,
                max_value="1000",
                title_keyword=keyword,
                wait_after_apply_ms=8000,
                picker_within_years=2,
                try_read_updated_revenue=True,
            )
            run_results["competitors_flow"]["raw_result"] = result
            pb = result.get("picker_best") or {}
            if pb.get("url") and pb.get("product_details") and pb.get("parent_level_revenue"):
                run_results["competitors_flow"]["picker_best"] = pb
                COMPETITOR_PRODUCT_URL = pb["url"]
                break
            else:
                raise ValueError("No qualifying product found in CSV.")
        except Exception as e:
            msg = f"competitors_flow attempt {attempt} failed: {e}"
            print("[ERROR]", msg)
            run_results["errors"].append(msg)
            if attempt == MAX_RETRIES:
                print("[ERROR] Competitors flow: max retries reached.")
        finally:
            # cleanup competitor CSVs
            for file in os.listdir(COMPETITORS_DOWNLOAD_DIR):
                if file.endswith(".csv"):
                    try: os.remove(os.path.join(COMPETITORS_DOWNLOAD_DIR, file))
                    except Exception: pass

    # ---- Profitability metrics (retry, only if we got a competitor URL) ----
    if COMPETITOR_PRODUCT_URL:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print("[Info] Getting Profitability Calculator metrics.")
                metrics = get_profitability_metrics(
                    browser,
                    product_url=COMPETITOR_PRODUCT_URL,
                    wait_secs=25,
                    close_all_tabs_first=False,
                    close_others_after_open=True,
                )
                for k in run_results["profitability_metrics"]:
                    run_results["profitability_metrics"][k]["text"]   = metrics[k]["text"]
                    run_results["profitability_metrics"][k]["number"] = metrics[k]["number"]
                break
            except Exception as e:
                msg = f"profitability_metrics attempt {attempt} failed: {e}"
                print("[ERROR]", msg)
                run_results["errors"].append(msg)
                if attempt == MAX_RETRIES:
                    print("[ERROR] Profitability: max retries reached.")

    # ---- Cerebro: extract ASIN, search keyword, export CSV, GPT step ----
    asin_match = re.search(r"/dp/([A-Z0-9]{10})", product_url)
    ASIN = asin_match.group(1) if asin_match else None
    if not ASIN:
        msg = "[WARN] Could not parse ASIN from product_url; skipping Cerebro."
        print(msg)
        run_results["errors"].append(msg)
    else:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print("[Info] Cerebro flow.")
                product_page = open_amazon_page(ctx, product_url)
                cerebro_tab = open_cerebro_from_xray(browser, product_page, ASIN, timeout_s=35)
                cerebro_search(cerebro_tab, keyword)

                csv_path = export_cerebro_csv(
                    cerebro_tab,
                    CEREBRO_DOWNLOAD_DIR,
                    filename_hint=f"cerebro_{ASIN}_{keyword}.csv"
                )
                print("[DONE] Cerebro CSV saved to:", csv_path)

                user_prompt, search_volumes = get_keywords_volumes_from_csv(csv_path)
                run_results["keywords_volumes"]["user_prompt"]    = user_prompt
                run_results["keywords_volumes"]["search_volumes"] = search_volumes

                projections = get_gpt_response(user_prompt, search_volumes)
                run_results["gpt_projection"]["response"] = projections
                break
            except Exception as e:
                msg = f"cerebro attempt {attempt} failed: {e}"
                print("[ERROR]", msg)
                run_results["errors"].append(msg)
                if attempt == MAX_RETRIES:
                    print("[ERROR] Cerebro: max retries reached.")
            finally:
                for file in os.listdir(CEREBRO_DOWNLOAD_DIR):
                    if file.endswith(".csv"):
                        try: os.remove(os.path.join(CEREBRO_DOWNLOAD_DIR, file))
                        except Exception: pass
    try:
        for p in ctx.pages:
            try:
                p.close()
            except Exception:
                pass
    except Exception:
        pass

    # teardown for this product
    try:
        browser.close()
    except Exception:
        pass
    try:
        pw.stop()
    except Exception:
        pass

    return run_results


# ---------------------------
# Payload processor
# ---------------------------
def process_brands(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload format (Python dict from frontend JSON):
    {
      "brands": [
        {
          "brand": "...",
          "countries": [
            {
              "name": "US",
              "products": [
                { "productname": "...", "url": "...", "keyword": "...", "categoryUrl": "..." },
                ...
              ]
            },
            ...
          ]
        }
      ]
    }
    """
    out: Dict[str, Any] = {"runs": []}

    for b in payload.get("brands", []):
        brand_name = (b.get("brand") or "").strip()
        brand_block = {"brand": brand_name, "countries": []}

        for c in b.get("countries", []):
            country_name = (c.get("name") or "").strip()
            country_block = {"name": country_name, "products": []}

            for p in c.get("products", []):
                productname = p.get("productname") or ""
                product_url = p.get("url") or ""
                keyword     = p.get("keyword") or ""
                categoryUrl = p.get("categoryUrl") or ""

                # Run full pipeline for this product
                result = run_single_product(
                    category_url=categoryUrl,
                    product_url=product_url,
                    keyword=keyword
                )

                country_block["products"].append({
                    "productname": productname,
                    "url": product_url,
                    "keyword": keyword,
                    "categoryUrl": categoryUrl,
                    "result": result
                })

            brand_block["countries"].append(country_block)
        out["runs"].append(brand_block)

    return out

# ---------------------------
# Main function for backend integration
# ---------------------------
def run_scraper_main(payload):
    """
    Main function to run the scraper with payload from backend
    Returns: dict with results and status
    """
    try:
        print(f"[INFO] Starting scraper with {len(payload.get('brands', []))} brands")
        
        results = process_brands(payload)

        # Persist full run snapshot
        with open("full_runs.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print("[DONE] All runs complete. Saved to full_runs.json")
        
        print("\n[Info] Logging to googlesheet")
        try:
            write_results_to_country_tabs(results)
            print("[SUCCESS] Results logged to Google Sheets")
        except Exception as e:
            print(f"[WARNING] Error logging to sheets: {e}")
            
        return {
            "success": True,
            "results": results,
            "message": "Scraper completed successfully"
        }
            
    except Exception as e:
        error_msg = f"[ERROR] Failed to process brands: {e}"
        print(error_msg)
        return {
            "success": False,
            "error": str(e),
            "message": "Scraper failed"
        }

# ---------------------------
# Standalone entrypoint (for testing)
# ---------------------------
if __name__ == "__main__":
    import sys
    
    try:
        # Read payload from stdin (sent by Node.js backend)
        payload_json = sys.stdin.read()
        if not payload_json.strip():
            print("[ERROR] No payload received from stdin")
            sys.exit(1)
            
        payload = json.loads(payload_json)
        print(f"[INFO] Received payload with {len(payload.get('brands', []))} brands")
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON payload: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to read payload: {e}")
        sys.exit(1)

    # Run the main function
    result = run_scraper_main(payload)
    
    if not result["success"]:
        sys.exit(1)



# payload = {
#                 "brands": [
#                     {
#                     "brand": 'Big wipes ',
#                     "countries": [
#                         {
#                         "name": 'UK',
#                         "products": [
#                             {
#                             "productname": 'WILSON NFL Super Grip Composite Footballs',
#                             "url": 'https://www.amazon.com/Wilson-Super-Grip-Official-Football/dp/B0012SNLJG/ref=sr_1_1?crid=11N4YAPWDPUF1&dib=eyJ2IjoiMSJ9.VFtpRBXpX0rlGNlPl2X6F_ab989t9a323UfwzuNlhpbtkOqD-aubFTI4dAX36PwIXH7cLX7awRpXDQb6-IG3V_VmUb3FmmkC9xgCLVouC3tetG6k0jSvuBtaNGEBvomgUd8jINBfqaATt9DrujyS01gNneur4LpTIpMnZEp4lQwhUdDyH3h6e93SrJZwLtfHfWetsXNSmcodkCPIWGQ7Ma1gOVeqLrBvxsPtvzsMOjisBhY8i0gazoPWVw9_rph6tc4Ycuva4Q0KZtPeMayX1Gl1-AY900Z7aQ1wVcfKEqs.yezBLzNWMR_sl6Maz5gxBkqrSWK93IBjwUEN_UBBmIE&dib_tag=se&keywords=football&qid=1755186151&sprefix=football%2Caps%2C1829&sr=8-1&th=1',
#                             "keyword": 'football',
#                             "categoryUrl": 'https://www.amazon.com/s?k=football&crid=11N4YAPWDPUF1&sprefix=football%2Caps%2C1829&ref=nb_sb_noss_1'
#                             },
#                             {
#                             "productname": 'Nike Academy Football FZ2966',
#                             "url": 'https://www.amazon.com/NIKE-Unisex-Adult-Academy-Football-Blackened/dp/B0DBLQGGWV/ref=sr_1_1?dib=eyJ2IjoiMSJ9.fMvEXwDDobQKyHb8bN2vIa9swZN8acN-V2FC0niqgji0aIEDmHtOtP69KSO-Yq84Lq3fW3C6yKHw7cGcoB-dF8zueQ4sk8Q3tOCdPiGy23dSE_2naiedFFEjN1r27N6AxX0lZtHnyHBgduXqErcvEn40fWlInIF1AjkryeMYPzkc0ZNy0A75voRcr5hnu61ylYqCuqF4izcOTGpft9arlitT2tSXdcECi0CChwglFSjx34x8wA8CnDtDFqN4NV-6ux-cI3DkLSmwHxQy4h7L6jz2OYHo_9tsICI8noZBK2M.wGmZLOtX3hxtxNulQlpUwsfE5UOVUnreMUMpn6yrGb8&dib_tag=se&keywords=soccer+ball&qid=1755186233&sr=8-1',
#                             "keyword": 'soccer ball',
#                             "categoryUrl": 'https://www.amazon.com/s?k=soccer+ball&ref=nb_sb_noss'
#                             }
#                         ]
#                         },
#                     ]
#                     }
#                 ]
# }