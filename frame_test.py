from auth import open_browser
from scraper import _navigate

URL = "https://app.kalvium.community/livebooks/2635/058d6e95-732c-4750-9fb9-e09e7ca14f6c"

with open_browser() as (_, page):
    _navigate(page, URL)

    # Open the lesson
    page.get_by_role("button", name="Lesson").click()

    page.wait_for_timeout(5000)

    print("\n===== FRAMES =====")

    for i, frame in enumerate(page.frames):
        print(f"\nFrame {i}")
        print("URL:", frame.url)

        try:
            text = frame.locator("body").inner_text(timeout=3000)
            print(text[:1000])
        except Exception as e:
            print("Cannot read:", e)

    input("\nPress Enter to close...")