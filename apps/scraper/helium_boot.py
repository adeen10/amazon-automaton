# # helium_boot.py
# import sys, time, socket, subprocess
# from pathlib import Path
# from urllib.request import urlopen
# from urllib.error import URLError
# from playwright.sync_api import sync_playwright

# def _find_free_port() -> int:
#     s = socket.socket(); s.bind(("127.0.0.1", 0))
#     port = s.getsockname()[1]; s.close(); return port

# def _cdp_ready(port: int) -> bool:
#     try:
#         with urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5) as r:
#             return r.status == 200
#     except Exception:
#         return False

# def boot_and_xray(
#     *,
#     chrome_path: str,
#     user_data_dir: str,
#     profile_dir: str = "Profile 4",
#     ext_id: str,
#     target_url: str,
#     seed_url: str = "https://google.com",
#     cdp_port: int | None = 9666,       # set None for auto-free port
#     open_extensions_page: bool = True, # try to open chrome://extensions too
#     wait_secs: int = 20
# ):
#     """
#     Launches Chrome with remote debugging, connects Playwright, opens:
#       1) seed tab (optional),
#       2) extension popup tab: chrome-extension://<ext_id>/popup.html,
#       3) (optional) chrome://extensions,
#       4) sends message {type:'open-page-and-xray', params:{url: target_url}}
#          and waits for an Amazon results tab to appear.
#     Returns: (playwright, browser, context, target_page)
#     Caller is responsible to close playwright/browser when done.
#     """
#     chrome = Path(chrome_path)
#     if not chrome.exists():
#         raise FileNotFoundError(f"Chrome not found: {chrome_path}")

#     udd = Path(user_data_dir); udd.mkdir(parents=True, exist_ok=True)

#     # pick/confirm port
#     if cdp_port is None:
#         cdp_port = _find_free_port()

#     # reuse if already listening
#     if not _cdp_ready(cdp_port):
#         print(f"[info] Launching Chrome on port {cdp_port}...")
#         args = [
#             str(chrome),
#             f"--remote-debugging-port={cdp_port}",
#             f"--user-data-dir={user_data_dir}",
#             f"--profile-directory={profile_dir}",
#             "--no-first-run",
#             "--no-default-browser-check",
#             seed_url,
#         ]
#         creationflags = 0
#         if sys.platform.startswith("win"):
#             creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
#         subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creationflags)

#         # wait for CDP to come up
#         deadline = time.time() + 25
#         while time.time() < deadline and not _cdp_ready(cdp_port):
#             time.sleep(0.2)
#         if not _cdp_ready(cdp_port):
#             raise TimeoutError(f"CDP not ready on 127.0.0.1:{cdp_port}")
#         print(f"[info] Chrome launched and CDP ready on {cdp_port}")
#     else:
#         print(f"[info] Reusing existing Chrome CDP on {cdp_port}")

#     cdp_url = f"http://127.0.0.1:{cdp_port}"
#     popup_url = f"chrome-extension://{ext_id}/popup.html"

#     print("[info] Connecting Playwright to Chrome...")
#     pw = sync_playwright().start()
#     browser = pw.chromium.connect_over_cdp(cdp_url)
#     ctx = browser.contexts[0] if browser.contexts else browser.new_context()

#     # 1) extension popup
#     popup = ctx.new_page()
#     popup.goto(popup_url, wait_until="domcontentloaded")
#     print("[info] Opened Helium popup tab.")

#     # 2) tell background to open + XRAY the target URL
#     popup.evaluate(
#         """(targetUrl) => new Promise((resolve) => {
#             chrome.runtime.sendMessage(
#                 { type: "open-page-and-xray", params: { url: targetUrl } },
#                 () => resolve(true)
#             );
#         })""",
#         target_url,
#     )
#     print(f"[info] Sent background message: open-page-and-xray for {target_url}")

#     # wait for Helium-activated results tab
#     target_page = None
#     deadline = time.time() + wait_secs
#     while time.time() < deadline and target_page is None:
#         for pg in ctx.pages:
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
#         print("[warn] Could not detect the Helium-opened Amazon tab within wait time.")

#     return pw, browser, ctx, target_page


# helium_boot.py
# import sys, time, socket, subprocess
# from pathlib import Path
# from urllib.request import urlopen
# from urllib.error import URLError
# from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# def _find_free_port() -> int:
#     s = socket.socket(); s.bind(("127.0.0.1", 0))
#     port = s.getsockname()[1]; s.close(); return port

# def _cdp_ready(port: int) -> bool:
#     try:
#         with urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5) as r:
#             return r.status == 200
#     except Exception:
#         return False

# def boot_and_xray(
#     *,
#     chrome_path: str,
#     user_data_dir: str,
#     profile_dir: str = "Profile 4",
#     ext_id: str,
#     target_url: str,
#     cdp_port: int | None = 9666,      # None => auto free port
#     wait_secs: int = 20,
#     popup_visible: bool = False       # keep popup hidden: open -> send -> close
# ):
#     """
#     Launch Chrome (CDP), connect Playwright, trigger Helium XRAY for target_url,
#     and return as soon as 'Search Volume' is visible on the results page.

#     Returns: (playwright, browser, context, target_page)
#     Caller closes browser/pw.
#     """
#     chrome = Path(chrome_path)
#     if not chrome.exists():
#         raise FileNotFoundError(f"Chrome not found: {chrome_path}")

#     udd = Path(user_data_dir); udd.mkdir(parents=True, exist_ok=True)

#     # pick/confirm port
#     if cdp_port is None:
#         cdp_port = _find_free_port()

#     # launch if not already listening
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

#     cdp_url  = f"http://127.0.0.1:{cdp_port}"
#     popup_url = f"chrome-extension://{ext_id}/popup.html"

#     print("[info] Connecting Playwright to Chrome...")
#     pw = sync_playwright().start()
#     browser = pw.chromium.connect_over_cdp(cdp_url)
#     ctx = browser.contexts[0] if browser.contexts else browser.new_context()

#     # Open extension popup just to send the message
#     popup = ctx.new_page()
#     popup.goto(popup_url, wait_until="domcontentloaded")
#     print("[info] Opened Helium popup (transient).")

#     popup.evaluate(
#         """(targetUrl) => new Promise((resolve) => {
#             chrome.runtime.sendMessage(
#                 { type: "open-page-and-xray", params: { url: targetUrl } },
#                 () => resolve(true)
#             );
#         })""",
#         target_url,
#     )
#     print(f"[info] Sent background message: open-page-and-xray for {target_url}")

#     # Close popup if user wants minimal UI
#     if not popup_visible:
#         try:
#             popup.close()
#             print("[info] Closed Helium popup tab (minimal UI).")
#         except Exception:
#             pass

#     # Wait for Amazon tab to appear
#     target_page = None
#     deadline = time.time() + wait_secs
#     while time.time() < deadline and target_page is None:
#         for pg in ctx.pages:
#             if pg.url.startswith("https://www.amazon.com/s?"):
#                 target_page = pg
#                 break
#         if target_page: break
#         time.sleep(0.25)

#     if not target_page:
#         print("[warn] Could not detect the Helium-opened Amazon tab within wait time.")
#         return pw, browser, ctx, None

#     target_page.bring_to_front()
#     print("[info] Amazon results tab detected; waiting for Search Volume...")

#     def _wait_for_search_volume(page, total_timeout_ms: int) -> bool:
#         """Return True as soon as the 'Search Volume' widget is visible (label + numeric nearby)."""
#         t_end = time.time() + total_timeout_ms / 1000

#         # 1) Most specific (your class): fast path
#         try:
#             page.locator("div.sc-btFlzp.fOTooS:has-text('Search Volume')").first.wait_for(
#                 state="visible", timeout=min(3000, total_timeout_ms)
#             )
#             return True
#         except PWTimeout:
#             pass

#         # 2) Text-based but non-strict: pick a single node (.first) to avoid strict mode
#         try:
#             page.get_by_text("Search Volume", exact=True).first.wait_for(
#                 timeout=min(3000, total_timeout_ms)
#             )
#             # Optional: verify there is a number near the label (means stats are actually rendered)
#             el = page.get_by_text("Search Volume", exact=True).first.element_handle()
#             if el:
#                 has_num = page.evaluate(
#                     """
#                     (labelEl) => {
#                     const numRe = /(?:\\d{1,3}(?:,\\d{3})+|\\d+)(?:\\.\\d+)?/;
#                     let root = labelEl.parentElement;
#                     for (let i = 0; i < 5 && root; i++) {
#                         const txt = (root.innerText || "").replace(/\\s+/g, " ").trim();
#                         if (numRe.test(txt)) return true;
#                         root = root.parentElement;
#                     }
#                     return false;
#                     }
#                     """,
#                     el,
#                 )
#                 if has_num:
#                     return True
#         except PWTimeout:
#             pass

#         # 3) Poll the DOM (fallback) for label + number combo
#         while time.time() < t_end:
#             ok = page.evaluate(
#                 """
#                 () => {
#                 const numRe = /(?:\\d{1,3}(?:,\\d{3})+|\\d+)(?:\\.\\d+)?/;
#                 const nodes = Array.from(document.querySelectorAll("*"));
#                 for (const n of nodes) {
#                     const t = (n.innerText || "").trim();
#                     if (t === "Search Volume" || /\\bSearch Volume\\b/.test(t)) {
#                     let root = n.parentElement;
#                     for (let i = 0; i < 5 && root; i++) {
#                         const txt = (root.innerText || "").trim();
#                         if (numRe.test(txt)) return true;
#                         root = root.parentElement;
#                     }
#                     }
#                 }
#                 return false;
#                 }
#                 """
#             )
#             if ok:
#                 return True
#             time.sleep(0.25)

#         return False

#     ok = _wait_for_search_volume(target_page, wait_secs * 1000)
#     if ok:
#         print("[SUCCESS] Search Volume detected. XRAY finished & stats visible.")
#     else:
#         print("[warn] Search Volume did not appear before timeout. XRAY may still be running.")


import sys, time, socket, subprocess
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
from playwright.sync_api import sync_playwright

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


