import sys, time, socket, subprocess
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PWTimeout

def _wait_for_xray_panel(page, timeout_ms: int = 20000) -> bool:
    """
    Return True when the Xray overlay + some grid text is visible.
    """
    try:
        page.wait_for_selector("#h10-style-container .react-draggable.resizable",
                               state="visible", timeout=timeout_ms)
    except PWTimeout:
        return False

    # Try a few headers that typically appear
    for header in ("BSR", "Revenue", "Price"):
        try:
            page.wait_for_selector(f"text={header}", state="visible", timeout=2500)
            return True
        except PWTimeout:
            continue
    # Panel is visible; headers not found yet—consider it OK to proceed
    return True


def _open_xray_via_widget(page, *, inject_settle_ms: int = 1500, menu_timeout_ms: int = 15000,
                          panel_timeout_ms: int = 20000) -> bool:
    """
    Hover the left Helium widget, click 'Xray — Amazon Product Research', wait for panel.
    Returns True if panel detected; False otherwise.
    """
    # Let extension inject
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(inject_settle_ms)

    # Hover the small widget to reveal the menu
    try:
        widget_svg = page.locator("#h10-page-widget svg").first
        widget_svg.wait_for(state="visible", timeout=menu_timeout_ms)
    except PWTimeout:
        return False

    box = widget_svg.bounding_box()
    if not box:
        return False

    page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
    widget_svg.hover(force=True)
    page.wait_for_timeout(300)
    page.mouse.move(box["x"] + box["width"]/2, box["y"] + 6)
    page.wait_for_timeout(120)

    # Ensure the menu appeared; fallback to synthetic mouseenter if needed
    try:
        page.wait_for_selector('text=Xray — Amazon Product Research', state='visible', timeout=2500)
    except PWTimeout:
        try:
            page.evaluate("""sel => {
                const el = document.querySelector(sel);
                if (el) el.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
            }""", "#h10-page-widget svg")
            page.wait_for_selector('text=Xray — Amazon Product Research', state='visible', timeout=5000)
        except PWTimeout:
            return False

    # Click the button (role-based first; text fallback)
    try:
        btn = page.get_by_role("button", name="Xray — Amazon Product Research")
        if btn.is_visible():
            btn.click()
        else:
            page.locator("div", has_text="Xray — Amazon Product Research").first.click()
    except Exception:
        return False

    return _wait_for_xray_panel(page, timeout_ms=panel_timeout_ms)


def _open_xray_via_extension(ctx, *, ext_id: str, target_url: str,
                             popup_visible: bool = False, wait_secs: int = 20):
    """
    Use the extension popup to instruct Helium to open the Amazon results page and run Xray.
    Returns (page or None). Does NOT guarantee panel visibility—only opens the tab.
    """
    popup_url = f"chrome-extension://{ext_id}/popup.html"
    popup = ctx.new_page()
    popup.goto(popup_url, wait_until="domcontentloaded")
    try:
        popup.evaluate(
            """(targetUrl) => new Promise((resolve) => {
                chrome.runtime.sendMessage(
                    { type: "open-page-and-xray", params: { url: targetUrl } },
                    () => resolve(true)
                );
                setTimeout(() => resolve(false), 50000);
            })""",
            target_url,
        )
    except Exception:
        # Popup eval can fail if service worker isn't active; treat as no-op and fallback later
        pass

    if not popup_visible:
        try: popup.close()
        except Exception: pass

    # Find the Amazon results tab Helium should have opened
    target_page = None
    deadline = time.time() + wait_secs
    while time.time() < deadline and target_page is None:
        for pg in ctx.pages:
            url = pg.url or ""
            if url.startswith("https://www.amazon.") and "/s?" in url:
                target_page = pg
                break
        if target_page:
            break
        time.sleep(0.25)

    if target_page:
        try: target_page.bring_to_front()
        except Exception: pass
    return target_page


def _find_free_port() -> int:
    s = socket.socket(); s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]; s.close(); return port

def _cdp_ready(port: int) -> bool:
    try:
        with urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False

def boot_and_xray(
    *,
    chrome_path: str,
    user_data_dir: str,
    profile_dir: str = "Profile 4",
    ext_id: str,
    target_url: str,
    cdp_port: int | None = 9666,      # None => auto free port
    wait_secs: int = 20,
    popup_visible: bool = False       # open -> send -> (optionally) close
):
    """
    Launch Chrome (CDP), connect Playwright, trigger Helium XRAY for target_url,
    and return as soon as the Amazon results tab is detected.

    Returns: (playwright, browser, context, target_page)
    """
    chrome = Path(chrome_path)
    if not chrome.exists():
        raise FileNotFoundError(f"Chrome not found: {chrome_path}")

    udd = Path(user_data_dir); udd.mkdir(parents=True, exist_ok=True)

    if cdp_port is None:
        cdp_port = _find_free_port()

    if not _cdp_ready(cdp_port):
        print(f"[info] Launching Chrome on port {cdp_port}...")
        args = [
            str(chrome),
            f"--remote-debugging-port={cdp_port}",
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

        deadline = time.time() + 25
        while time.time() < deadline and not _cdp_ready(cdp_port):
            time.sleep(0.2)
        if not _cdp_ready(cdp_port):
            raise TimeoutError(f"CDP not ready on 127.0.0.1:{cdp_port}")
        print(f"[info] Chrome launched and CDP ready on {cdp_port}")
    else:
        print(f"[info] Reusing existing Chrome CDP on {cdp_port}")

    cdp_url  = f"http://127.0.0.1:{cdp_port}"
    popup_url = f"chrome-extension://{ext_id}/popup.html"

    print("[info] Connecting Playwright to Chrome...")
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(cdp_url)
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()

    # Open extension popup just to send the message
    popup = ctx.new_page()
    popup.goto(popup_url, wait_until="domcontentloaded")
    print("[info] Opened Helium popup (transient).")

    popup.evaluate(
        """(targetUrl) => new Promise((resolve) => {
            chrome.runtime.sendMessage(
                { type: "open-page-and-xray", params: { url: targetUrl } },
                () => resolve(true)
            );
            setTimeout(() => resolve(false), 50000); // force resolve after 50s
        })""",
        target_url,
    )
    print(f"[info] Sent background message: open-page-and-xray for {target_url}")

    if not popup_visible:
        try:
            popup.close()
            print("[info] Closed Helium popup tab (minimal UI).")
        except Exception:
            pass

    # Wait for Amazon results tab to appear (simple wait)
    target_page = None
    deadline = time.time() + wait_secs
    while time.time() < deadline and target_page is None:
        for pg in ctx.pages:
            if pg.url.startswith("https://www.amazon.com/s?"):
                target_page = pg
                break
        if target_page:
            break
        time.sleep(0.25)

    if target_page:
        target_page.bring_to_front()
        print("[SUCCESS] Amazon tab for XRAY is active. Helium should be running now.")
    else:
        print("[warn] Could not detect the Helium-opened Amazon tab within wait time.")

    return pw, browser, ctx, target_page



# def boot_and_xray(
#     *,
#     chrome_path: str,
#     user_data_dir: str,
#     profile_dir: str = "Profile 4",
#     ext_id: str,
#     target_url: str,
#     cdp_port: int | None = 9666,      # None => auto free port
#     wait_secs: int = 20,
#     popup_visible: bool = False
# ):
#     """
#     Launch Chrome (CDP), connect Playwright, try extension path first,
#     fall back to widget-hover path if needed.
#     Returns: (playwright, browser, context, target_page)
#     """
#     chrome = Path(chrome_path)
#     if not chrome.exists():
#         raise FileNotFoundError(f"Chrome not found: {chrome_path}")

#     udd = Path(user_data_dir); udd.mkdir(parents=True, exist_ok=True)
#     if cdp_port is None:
#         cdp_port = _find_free_port()

#     if not _cdp_ready(cdp_port):
#         print(f"[info] Launching Chrome on port {cdp_port}...")
#         args = [
#             str(chrome),
#             f"--remote-debugging-port={cdp_port}",
#             f"--user-data-dir={user_data_dir}",
#             f"--profile-directory={profile_dir}",
#             "--no-first-run",
#             "--no-default-browser-check",
#             "about:blank",
#         ]
#         creationflags = 0
#         if sys.platform.startswith("win"):
#             creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
#         subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creationflags)

#         deadline = time.time() + 25
#         while time.time() < deadline and not _cdp_ready(cdp_port):
#             time.sleep(0.2)
#         if not _cdp_ready(cdp_port):
#             raise TimeoutError(f"CDP not ready on 127.0.0.1:{cdp_port}")
#         print(f"[info] Chrome launched and CDP ready on {cdp_port}")
#     else:
#         print(f"[info] Reusing existing Chrome CDP on {cdp_port}")

#     cdp_url = f"http://127.0.0.1:{cdp_port}"
#     print("[info] Connecting Playwright to Chrome...")
#     pw = sync_playwright().start()
#     browser = pw.chromium.connect_over_cdp(cdp_url)
#     ctx = browser.contexts[0] if browser.contexts else browser.new_context()

#     # --- Attempt 1: Extension message path ---
#     print("[info] Attempting Xray via extension message...")
#     target_page = _open_xray_via_extension(ctx, ext_id=ext_id, target_url=target_url,
#                                            popup_visible=popup_visible, wait_secs=wait_secs)

#     if not target_page:
#         # If Helium didn’t open it, navigate ourselves
#         print("[warn] Extension did not open Amazon tab; navigating directly...")
#         target_page = ctx.new_page()
#         try:
#             target_page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
#         except PWTimeout:
#             target_page.goto(target_url, wait_until="domcontentloaded", timeout=45000)

#     # Confirm if panel is already visible (sometimes extension auto-opens it)
#     if _wait_for_xray_panel(target_page, timeout_ms=8000):
#         print("[SUCCESS] Xray panel detected (extension path).")
#         return pw, browser, ctx, target_page

#     # --- Attempt 2: Widget-hover fallback ---
#     print("[info] Falling back to widget hover → click 'Xray — Amazon Product Research'...")
#     ok = _open_xray_via_widget(target_page, inject_settle_ms=1500, menu_timeout_ms=15000, panel_timeout_ms=20000)
#     if ok:
#         print("[SUCCESS] Xray panel opened via widget fallback.")
#         return pw, browser, ctx, target_page

#     print("[warn] Xray panel not detected after both strategies.")
#     # We still return (so your later steps can attempt and handle), but you can raise if you prefer:
#     # raise RuntimeError("xray not detected after extension + widget fallback")
#     return pw, browser, ctx, target_page
