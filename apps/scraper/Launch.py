# # command to run chrome profile
# # PS Adeen:C:\WINDOWS\system32> & "C:\Users\Al-Wajid Laptops\AppData\Local\Google\Chrome\Application\chrome.exe" `       
# # >>   --remote-debugging-port=9666 `                                                                                    
# # >>   --user-data-dir="C:\Users\Al-Wajid Laptops\automation-profile" `                                                  
# # >>   --profile-directory="Profile 4" `                                                                                 
# # >>   "https://google.com"  

# & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\USERNAME\automation-profile" --profile-directory="Profile 4"

# Launch.py
import os,re
from helium_boot import boot_and_xray
from getCategoryRev import get_category_revenue
from competitors import run_competitors_flow
from monthlyrev import get_first_product_monthly_revenue
from profitcal import get_profitability_metrics
from cerebro import open_amazon_page, open_cerebro_from_xray, cerebro_search, export_cerebro_csv
from gpt import get_keywords_volumes_from_csv, get_gpt_response


# USERNAME = "Al-Wajid Laptops"
USERNAME = "Hurai"
# CHROME_PATH   = rf"C:\Users\{USERNAME}\AppData\Local\Google\Chrome\Application\chrome.exe"
CHROME_PATH   = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = rf"C:\Users\{USERNAME}\automation-profile"
PROFILE_DIR   = "Profile 4"
EXT_ID        = "njmehopjdpcckochcggncklnlmikcbnb"
AMAZON_CATEGORY_URL    = "https://www.amazon.com/s?k=candy&crid=123SGIE3DMQW2&sprefix=ca%2Caps%2C701&ref=nb_sb_noss_2"
AMAZON_PRODUCT_URL = "https://www.amazon.com/MILKY-SNICKERS-Original-Minis-Candy/dp/B0CHXYTJS9/ref=sr_1_2?crid=26439MC7U5HX6&dib=eyJ2IjoiMSJ9.TPcizlUQLzOS5y9so-JAk2IfwpU9NoVq_aXwzhuAwYibJlzXoovPGeVNhAJhK_aB-JuF3yJx4uZu1tJT4yFXeawobePuCbNE5pcbUe1JJsu-LMRH0xr_NciRMI08DLZcMVBtfCfXKKQmhHjL2SRMUME4vUVBKVa-lNOrGv1zjjiB7WrcT-shILnsnZNtOfqX1lyfalUwCD97-FVNLpl65EjvUX8WELZdN8CVQKQXtjM82kz-GST91iDh0yRg8cD-zJemz_og8UFY43e2QYSLVnRUdiGIsY-766DgC7dmfzw.g6WLItJfQAxnVd1uKpMJXySL_FsnY4U8Yw-vLTRlr4w&dib_tag=se&keywords=candy&qid=1755080495&sprefix=cand%2Caps%2C1023&sr=8-2&th=1"
KEYWORD = "candy" 
CEREBRO_DOWNLOAD_DIR = os.path.join(os.getcwd(), "exports", "cerebro")
COMPETITORS_DOWNLOAD_DIR = os.path.join(os.getcwd(), "exports")
print(CEREBRO_DOWNLOAD_DIR)
print(COMPETITORS_DOWNLOAD_DIR)
os.makedirs(CEREBRO_DOWNLOAD_DIR, exist_ok=True)
MAX_RETRIES = 3

pw, browser, ctx, target_page = boot_and_xray(
    chrome_path=CHROME_PATH,
    user_data_dir=USER_DATA_DIR,
    profile_dir=PROFILE_DIR,
    ext_id=EXT_ID,
    target_url=AMAZON_CATEGORY_URL,
    cdp_port=9666,              # or None for dynamic
    wait_secs=20
)
print("[ok] boot complete; XRAY should be running.")

print("[Info] Getting Category Revenue")

# 1) category revenue extractor
for attempt in range(1, MAX_RETRIES + 1):
    try:
        rev = get_category_revenue(browser, wait_after_click_ms=15000)
        # rev['text'] and rev['number'] are available if you want to persist them
        break  # Success, exit loop
    except Exception as e:
        print(f"[ERROR] Attempt {attempt} failed: {e}")
        # print(type(e), type(str(e)))
        if "xray not detected" in str(e).lower():
            print("[WARN] XRAY not detected, rebooting browser...")
            #close previously open browser and playwright session
            # [p.close() for p in browser.pages]
            all_pages = ctx.pages
            [p.close() for p in all_pages]
            browser.close()
            pw.stop()
            #open new browser and playwright session
            pw, browser, ctx, target_page = boot_and_xray(
                chrome_path=CHROME_PATH,
                user_data_dir=USER_DATA_DIR,
                profile_dir=PROFILE_DIR,
                ext_id=EXT_ID,
                target_url=AMAZON_CATEGORY_URL,
                cdp_port=9666,              # or None for dynamic
                wait_secs=20
            )
                        
        if attempt == MAX_RETRIES:
            print("[ERROR] Max retries reached. Exiting...")
        else:
            print(f"[INFO] Retrying ({attempt}/{MAX_RETRIES})...")
    
print("[Info] Getting Competitor Info .")

# # 2) Competitors flow
# for attempt in range(1, MAX_RETRIES + 1):
#     try:
#         result = run_competitors_flow(
#             browser,
#             download_dir=COMPETITORS_DOWNLOAD_DIR,
#             max_input_visible_index=7,   # 8th visible "Max" input
#             max_value="1000",
#             title_keyword= KEYWORD,
#             wait_after_apply_ms=8000,
#             picker_within_years=2,
#             try_read_updated_revenue=True,
#         )
#         break
#     except Exception as e:
#         print(f"[ERROR] Attempt {attempt} failed: {e}")
#         if attempt == MAX_RETRIES:
#             print("[ERROR] Max retries reached. Exiting...")
#         else:
#             print(f"[INFO] Retrying ({attempt}/{MAX_RETRIES})...")
    
# #cleanup - delete all csv files in exports folder
# for file in os.listdir(COMPETITORS_DOWNLOAD_DIR):
#     if file.endswith(".csv"):
#         os.remove(os.path.join(COMPETITORS_DOWNLOAD_DIR, file))

print("[Info] Getting Monthly Revenue (30-Day Revenue card).")
for attempt in range(1, MAX_RETRIES + 1):
    try:
        first_rev = get_first_product_monthly_revenue(
            browser,
            product_search_url=AMAZON_PRODUCT_URL,   # direct product URL
            ext_id=EXT_ID,                           # ignored now
            wait_secs=30,
            popup_visible=False,                     # ignored
            close_all_tabs_first=False,              # set True if you want a hard reset first
            close_others_after_open=True,            # leaves exactly one tab open
            close_seed_after_xray=True               # ignored
        )
        print("30-Day Revenue:", first_rev["text"], "| number:", first_rev["number"])
        break
    except Exception as e:
        print(f"[ERROR] Attempt {attempt} failed: {e}")
        if attempt == MAX_RETRIES:
            print("[ERROR] Max retries reached. Exiting...")
        else:
            print(f"[INFO] Retrying ({attempt}/{MAX_RETRIES})...")



print("[Info] Getting Profitability Calculator metrics.")
for attempt in range(1, MAX_RETRIES + 1):
    try:
        metrics = get_profitability_metrics(
            browser,
            product_url=AMAZON_PRODUCT_URL,   # <- uses your existing constant
            wait_secs=25,
            close_all_tabs_first=False,       # set True if you want a full reset before starting
            close_others_after_open=True,     # keeps exactly one tab open
        )
        print("FBA Fees:", metrics["fba_fees"]["text"], "| number:", metrics["fba_fees"]["number"])
        print("Storage Fee Jan–Sep:", metrics["storage_fee_jan_sep"]["text"], "| number:", metrics["storage_fee_jan_sep"]["number"])
        print("Storage Fee Oct–Dec:", metrics["storage_fee_oct_dec"]["text"], "| number:", metrics["storage_fee_oct_dec"]["number"])
        print("Product Price:", metrics["product_price"]["text"], "| number:", metrics["product_price"]["number"])
        break
    except Exception as e:
        print(f"[ERROR] Attempt {attempt} failed: {e}")
        if attempt == MAX_RETRIES:
            print("[ERROR] Max retries reached. Exiting...")
        else:
            print(f"[INFO] Retrying ({attempt}/{MAX_RETRIES})...")



# Extract ASIN from the product URL
m = re.search(r"/dp/([A-Z0-9]{10})", AMAZON_PRODUCT_URL)
ASIN = m.group(1) if m else None
if not ASIN:
    print("[WARN] Could not parse ASIN from AMAZON_PRODUCT_URL; skipping Cerebro.")
else:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 1) open product page (ensures XRAY/Cerebro link is present)
            product_page = open_amazon_page(ctx, AMAZON_PRODUCT_URL)

            # 2) open Cerebro (new tab or same tab)
            cerebro_tab = open_cerebro_from_xray(browser, product_page, ASIN, timeout_s=35)

            # 3) search the keyword, wait for results UI
            cerebro_search(cerebro_tab, KEYWORD)

            # 4) export CSV to your chosen folder
            csv_path = export_cerebro_csv(
                cerebro_tab,
                CEREBRO_DOWNLOAD_DIR,
                filename_hint=f"cerebro_{ASIN}_{KEYWORD}.csv"
            )
            print("[DONE] Cerebro CSV saved to:", csv_path)

            user_prompt, search_volumes = get_keywords_volumes_from_csv(csv_path)
            projections = get_gpt_response(user_prompt, search_volumes)
            print(projections)
            #cleanup - delete all csv files in exports/cerebro folder
            for file in os.listdir(CEREBRO_DOWNLOAD_DIR):
                if file.endswith(".csv"):
                    os.remove(os.path.join(CEREBRO_DOWNLOAD_DIR, file))
            break
        except Exception as e:
            print(f"[ERROR] Attempt {attempt} failed: {e}")
            if attempt == MAX_RETRIES:
                print("[ERROR] Max retries reached. Exiting...")
            else:
                print(f"[INFO] Retrying ({attempt}/{MAX_RETRIES})...")


input("Press Enter to disconnect…")
browser.close()
pw.stop()
