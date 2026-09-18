"""MCP-facing tool wrappers for Kalvium Livebooks."""
from kalvium.attendance import get_attendance
from kalvium.assessments import get_assessments
import time
from kalvium.calendar import get_schedule
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

def attendance(
    semester: int | None = None,
    month: int | None = None,
    year: int | None = None,
) -> dict:
    """Get Kalvium attendance, optionally filtered by semester and month."""
    return get_attendance(semester=semester, month=month, year=year)

def assessments() -> dict:
    """Get scheduled and completed Kalvium assessments."""
    return get_assessments()

def schedule() -> dict:
    """Get the current week's Kalvium class schedule."""
    return get_schedule()