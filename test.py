from scraper import get_lesson

URL = "https://app.kalvium.community/livebooks/2635/058d6e95-732c-4750-9fb9-e09e7ca14f6c"

html = get_lesson(URL)

print("Length:", len(html))
print(html[:1000])        # <-- add this temporarily

with open("lesson.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved lesson.html")