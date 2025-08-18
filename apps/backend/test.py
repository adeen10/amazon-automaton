import sys, time, socket, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# === YOUR CONSTANTS ===
EXT_ID        = "njmehopjdpcckochcggncklnlmikcbnb"
USERNAME      = "Al-Wajid Laptops"
CHROME_PATH   = rf"C:\Users\{USERNAME}\AppData\Local\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\cdp-profile\automation"   # this must be a Chrome profile folder (keep using it consistently)
PROFILE_DIR   = "Default"
CDP_PORT      = 9666
AMAZON_URL    = "https://www.amazon.com/s?k=candy&crid=1SVK5JELJ5CJ6&sprefix=cricket+bat%2Caps%2C2290&ref=nb_sb_noss_1"

def _cdp_ready(port:int)->bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.25):
            return True
    except OSError:
        return False

def _ensure_chrome_running(chrome_path:str, user_data_dir:str, profile_dir:str, port:int):
    chrome = Path(chrome_path)
    if not chrome.exists():
        raise FileNotFoundError(f"Chrome not found: {chrome_path}")
    Path(user_data_dir).mkdir(parents=True, exist_ok=True)

    if _cdp_ready(port):
        print(f"[info] Reusing existing Chrome at 127.0.0.1:{port}")
        return

    print(f"[info] Launching Chrome with CDP on {port} ...")
    # IMPORTANT: no --disable-extensions here. We want the real profile (with Helium already installed)
    args = [
        str(chrome),
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        f"--profile-directory={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank",
    ]
    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creationflags)

    # wait for CDP
    deadline = time.time() + 25
    while time.time() < deadline and not _cdp_ready(port):
        time.sleep(0.2)
    if not _cdp_ready(port):
        raise TimeoutError(f"CDP not ready on 127.0.0.1:{port}")

    print(f"[info] Chrome launched and CDP ready")

def _goto(page, url:str):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
    except PWTimeout:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)

def _open_xray(page):
    # give extension time to inject
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1500)

    # hover mini widget
    widget_svg = page.locator("#h10-page-widget svg").first
    widget_svg.wait_for(state="visible", timeout=15000)
    box = widget_svg.bounding_box()
    if not box:
        raise RuntimeError("Helium widget bbox not found")

    page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
    widget_svg.hover(force=True)
    page.wait_for_timeout(300)
    page.mouse.move(box["x"] + box["width"]/2, box["y"] + 6)
    page.wait_for_timeout(120)

    # ensure menu visible
    try:
        page.wait_for_selector('text=Xray — Amazon Product Research', state='visible', timeout=2500)
    except PWTimeout:
        page.evaluate("""sel => {
            const el = document.querySelector(sel);
            if (el) el.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
        }""", "#h10-page-widget svg")
        page.wait_for_selector('text=Xray — Amazon Product Research', state='visible', timeout=5000)

    # click the Xray button
    xray_btn = page.get_by_role("button", name="Xray — Amazon Product Research")
    if xray_btn.is_visible():
        xray_btn.click()
    else:
        page.locator("div", has_text="Xray — Amazon Product Research").first.click()

    # wait panel + a header
    page.wait_for_selector("#h10-style-container .react-draggable.resizable", state="visible", timeout=20000)
    for header in ("BSR", "Revenue", "Price"):
        try:
            page.wait_for_selector(f"text={header}", state="visible", timeout=4000)
            print(f"[info] Xray loaded (saw '{header}')")
            return
        except PWTimeout:
            pass
    print("[warn] Xray panel visible, but headers not detected yet.")

def main():
    _ensure_chrome_running(CHROME_PATH, USER_DATA_DIR, PROFILE_DIR, CDP_PORT)

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.pages[0] if context.pages else context.new_page()

        _goto(page, AMAZON_URL)
        _open_xray(page)

        print("✅ Xray opened. Keeping window for 60s...")
        page.wait_for_timeout(60000)
        browser.close()

if __name__ == "__main__":
    main()
