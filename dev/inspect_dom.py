from auth import open_browser

URL = "https://app.kalvium.community/livebooks/2635/a17520eb-a3bb-41b1-a2fb-4076fb2ae29b/lessons"

with open_browser() as (_, page):
    page.goto(URL, wait_until="load")

    page.wait_for_timeout(5000)

    print("===== IFRAMES =====")
    print(page.locator("iframe").count())

    print("\n===== BODY =====")
    print(page.locator("body").inner_text()[:5000])

    input("Press Enter...")