from scraper import get_lesson
from markdown import html_to_markdown

URL = "https://app.kalvium.community/livebooks/2635/058d6e95-732c-4750-9fb9-e09e7ca14f6c"

html = get_lesson(URL)

md = html_to_markdown(html)

print(md[:1000])

with open("lesson.md", "w", encoding="utf-8") as f:
    f.write(md)

print("Saved lesson.md")