"""MCP-facing tool wrappers for Kalvium Livebooks."""
import time
from scraper import Lesson, Livebook, get_lesson as scrape_lesson
from scraper import list_lessons as scrape_lessons
from scraper import list_livebooks as scrape_livebooks


def list_livebooks():

    start = time.time()
    result = scrape_livebooks()


    return result


def list_lessons(livebook_id: str) -> list[Lesson]:
    """List all lessons in a Livebook after expanding its module accordions."""
    return scrape_lessons(livebook_id)


def get_lesson(url: str) -> str:
    """Get a Kalvium lesson as Markdown suitable for a study assistant."""
    from markdown import html_to_markdown

    return html_to_markdown(scrape_lesson(url))

def hello() -> str:
    """Simple test tool."""
    return "Hello from Kalvium MCP!"