from playwright.sync_api import sync_playwright

LIVEBOOK = "https://app.kalvium.community/livebooks/2635"

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="./playwright-profile",
        channel="chrome",
        headless=False,
    )

    page = browser.new_page()
    page.goto(LIVEBOOK, wait_until="networkidle")

    # Expand every module
    for i in range(1, 10):   # Supports up to 9 modules
        try:
            page.get_by_role(
                "button",
                name=f"Module {i}"
            ).click(timeout=2000)

            print(f"Expanded Module {i}")
            page.wait_for_timeout(800)

        except Exception:
            print(f"Module {i} not found")

    print("\n===== LESSONS =====\n")

    links = page.locator("a[href^='/livebooks/2635/']")

    seen = set()

    for i in range(links.count()):
        href = links.nth(i).get_attribute("href")
        text = links.nth(i).inner_text().strip()

        if href and href not in seen:
            seen.add(href)
            print(text)
            print("https://app.kalvium.community" + href)
            print()

    input("Press Enter...")