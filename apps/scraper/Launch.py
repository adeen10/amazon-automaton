# # command to run chrome profile
# # PS Adeen:C:\WINDOWS\system32> & "C:\Users\Al-Wajid Laptops\AppData\Local\Google\Chrome\Application\chrome.exe" `       
# # >>   --remote-debugging-port=9666 `                                                                                    
# # >>   --user-data-dir="C:\Users\Al-Wajid Laptops\automation-profile" `                                                  
# # >>   --profile-directory="Profile 4" `                                                                                 
# # >>   "https://google.com"  

# Launch.py
import os,re
from helium_boot import boot_and_xray
from getCategoryRev import get_category_revenue
from competitors import run_competitors_flow
from monthlyrev import get_first_product_monthly_revenue
from profitcal import get_profitability_metrics
from cerebro import open_amazon_page, open_cerebro_from_xray, cerebro_search, export_cerebro_csv


CHROME_PATH   = r"C:\Users\Al-Wajid Laptops\AppData\Local\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\Users\Al-Wajid Laptops\automation-profile"
PROFILE_DIR   = "Profile 4"
EXT_ID        = "njmehopjdpcckochcggncklnlmikcbnb"
AMAZON_CATEGORY_URL    = "https://www.amazon.com/s?k=candy&crid=123SGIE3DMQW2&sprefix=ca%2Caps%2C701&ref=nb_sb_noss_2"
AMAZON_PRODUCT_URL = "https://www.amazon.com/MetaShot-Smart-Bat-TV-Connector/dp/B0CNQ4MDZY/ref=sr_1_1_sspa?crid=1ZCPCQZN6DZSY&dib=eyJ2IjoiMSJ9.nnJDH_7Nn7RV8V4iSvfYVAOBIydz6ULudL5roGigYGFT_Cb5D-j2o2h2w1ENrFeHfx3VBBHFWDpOX0FLB25u-4XRSkYNaam2CYIxj5Q5lb_pgoIXMMMVpVYST1avt5BSsM-NAzqL-n0lXiZ-3FbRLGcypWn4tbgSuF_NfyM2iN2_TfUPjlgGzh4xTKKQFkOY0c8ZxEXzRBUA-Q9wWV_ZwVITAPdbZWBYOw1As1_5ugbSSKSAr17yhiE4tL816vegnRIzViNhNUaCz-S-SnOD_h_zczZSPerRMEpyC20Ln2k.YuS4MK3hIjTdpHlf4p8pOBBlDM4gRbPKa1aZRRgubvU&dib_tag=se&keywords=cricket%2Bbat&qid=1755006246&sprefix=cricket%2B%2Caps%2C665&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1"
KEYWORD = "candy" 
CEREBRO_DOWNLOAD_DIR = r"E:\automation\exports\cerebro"
os.makedirs(CEREBRO_DOWNLOAD_DIR, exist_ok=True)

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
# Run the category revenue extractor using the same browser instance
try:
    rev = get_category_revenue(browser, wait_after_click_ms=15000)
    # rev['text'] and rev['number'] are available if you want to persist them
except Exception as e:
    print("[ERROR]", e)
    
print("[Info] Getting Competitor Info .")
# 2) Competitors flow
try:
    result = run_competitors_flow(
        browser,
        download_dir=r"E:\automation\exports",
        max_input_visible_index=7,   # 8th visible "Max" input
        max_value="1000",
        title_keyword= KEYWORD,
        wait_after_apply_ms=8000,
        picker_within_years=2,
        try_read_updated_revenue=True,
    )
    # You can use 'result' dict here (CSV path, picker_best, updated revenue, etc.)
except Exception as e:
    print("[ERROR] Competitors flow failed:", e)
    
print("[Info] Getting Monthly Revenue (30-Day Revenue card).")
first_rev = get_first_product_monthly_revenue(
    browser,
    product_search_url=AMAZON_PRODUCT_URL,   # direct product URL
    ext_id=EXT_ID,                           # ignored now
    wait_secs=20,
    popup_visible=False,                     # ignored
    close_all_tabs_first=False,              # set True if you want a hard reset first
    close_others_after_open=True,            # leaves exactly one tab open
    close_seed_after_xray=True               # ignored
)
print("30-Day Revenue:", first_rev["text"], "| number:", first_rev["number"])


print("[Info] Getting Profitability Calculator metrics.")
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


# Extract ASIN from the product URL
m = re.search(r"/dp/([A-Z0-9]{10})", AMAZON_PRODUCT_URL)
ASIN = m.group(1) if m else None
if not ASIN:
    print("[WARN] Could not parse ASIN from AMAZON_PRODUCT_URL; skipping Cerebro.")
else:
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


input("Press Enter to disconnect…")
browser.close()
pw.stop()
