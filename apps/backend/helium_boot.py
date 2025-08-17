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


