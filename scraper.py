"""Read-only Playwright scraping for the authenticated Kalvium Livebooks UI."""

import logging
import re
import sys
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError
from pydantic import BaseModel, Field

from auth import open_browser

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://app.kalvium.community"
LIVEBOOKS_URL = f"{BASE_URL}/livebooks"
NAVIGATION_TIMEOUT_MS = 30_000
MODULE_BUTTON_PATTERN = re.compile(r"^Module\s+\d+", re.IGNORECASE)
LIVEBOOK_PATH_PATTERN = re.compile(r"^/livebooks/(?P<id>[^/]+)/?$")


class Livebook(BaseModel):
    """A Livebook available to the authenticated user."""

    id: str = Field(description="Kalvium Livebook identifier.")
    title: str = Field(description="Display title of the Livebook.")
    url: str = Field(description="Absolute Kalvium Livebook URL.")


class Lesson(BaseModel):
    """A lesson within a Livebook."""

    id: str = Field(description="Kalvium lesson identifier.")
    title: str = Field(description="Display title of the lesson.")
    url: str = Field(description="Absolute Kalvium lesson URL.")


def _navigate(page: Page, url: str) -> None:
    """Navigate to a Kalvium page."""

    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=NAVIGATION_TIMEOUT_MS,
    )

    page.wait_for_load_state("load")

    if "/login" in urlparse(page.url).path:
        raise PermissionError(
            "Playwright profile is not logged into Kalvium."
        )


def _normalise_text(locator: Locator) -> str:
    """Return a locator's text with browser whitespace normalised."""
    return " ".join(locator.inner_text().split())


def _validate_livebook_id(livebook_id: str) -> str:
    """Validate a Livebook ID used to build a first-party Kalvium URL."""
    cleaned_id = livebook_id.strip()
    if not cleaned_id or "/" in cleaned_id or "?" in cleaned_id:
        raise ValueError("livebook_id must be a single non-empty URL path segment.")
    return cleaned_id


def _validate_lesson_url(url: str) -> str:
    """Ensure a supplied lesson URL belongs to the Kalvium Livebooks application."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "app.kalvium.community":
        raise ValueError("Lesson URL must use https://app.kalvium.community.")
    if not re.fullmatch(r"/livebooks/[^/]+/[^/]+/?", parsed.path):
        raise ValueError("URL must identify a Kalvium Livebook lesson.")
    return url


def list_livebooks() -> list[Livebook]:
    """Return Livebooks visible to the currently authenticated Kalvium account."""
    with open_browser() as (_, page):
        _navigate(page, LIVEBOOKS_URL)
        links = page.locator("a[href^='/livebooks/']")
        livebooks: list[Livebook] = []
        seen_ids: set[str] = set()

        for index in range(links.count()):
            link = links.nth(index)
            href = link.get_attribute("href")
            if not href:
                continue
            match = LIVEBOOK_PATH_PATTERN.fullmatch(href.split("?", 1)[0])
            if match is None or match["id"] in seen_ids:
                continue
            title = _normalise_text(link)
            if not title:
                continue
            livebook_id = match["id"]
            seen_ids.add(livebook_id)
            livebooks.append(
                Livebook(
                    id=livebook_id,
                    title=title,
                    url=urljoin(BASE_URL, href),
                )
            )

    LOGGER.info("Found %d Livebooks", len(livebooks))
    return livebooks


def list_lessons(livebook_id: str) -> list[Lesson]:
    """Expand every module in a Livebook and return each visible lesson once."""
    validated_id = _validate_livebook_id(livebook_id)
    course_url = f"{LIVEBOOKS_URL}/{validated_id}"
    lesson_selector = f"a[href^='/livebooks/{validated_id}/']"

    with open_browser() as (_, page):
        _navigate(page, course_url)

        # Newer Kalvium UI opens an overview page first.
        try:
            page.get_by_role("button", name="Go to Lessons").click(timeout=3000)
            page.wait_for_url(
                re.compile(rf"^{re.escape(course_url)}/lessons/?$"),
                timeout=NAVIGATION_TIMEOUT_MS,
            )
        except PlaywrightTimeoutError:
            # Already on the lessons page.
            pass

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)

        module_buttons = page.get_by_role("button", name=MODULE_BUTTON_PATTERN)
        module_count = module_buttons.count()

        if module_count == 0:
            raise RuntimeError("No Livebook module accordions were found on the page.")

        lessons: list[Lesson] = []
        seen_urls: set[str] = set()

        for index in range(module_count):
            button = module_buttons.nth(index)

            if button.get_attribute("aria-expanded") != "true":
                button.click()

            visible_links = page.locator(f"{lesson_selector}:visible")

            try:
                visible_links.first.wait_for(state="visible", timeout=2000)
            except PlaywrightTimeoutError:
                pass

            for lesson_index in range(visible_links.count()):
                link = visible_links.nth(lesson_index)

                href = link.get_attribute("href")
                if not href:
                    continue

                absolute_url = urljoin(BASE_URL, href)

                if absolute_url in seen_urls:
                    continue

                title = _normalise_text(link)
                if not title:
                    continue

                lesson_id = href.rstrip("/").rsplit("/", 1)[-1]

                seen_urls.add(absolute_url)
                lessons.append(
                    Lesson(
                        id=lesson_id,
                        title=title,
                        url=absolute_url,
                    )
                )

    LOGGER.info("Found %d lessons in Livebook %s", len(lessons), validated_id)
    return lessons


def get_lesson(url: str) -> str:
    """Return the dynamically mounted lesson body as an HTML fragment.

    Kalvium initially serves a lesson overview. Selecting its ``Go to Lessons``
    control routes to the lesson view, where the authored lesson is mounted in
    the single ``div.prose.max-w-none`` container.
    """
    lesson_url = _validate_lesson_url(url)

    with open_browser() as (_, page):
        _navigate(page, lesson_url)
        page.get_by_role("button", name="Go to Lessons").click()
        page.wait_for_url(
            re.compile(rf"^{re.escape(lesson_url)}/lessons/?$"),
            timeout=NAVIGATION_TIMEOUT_MS,
        )

        print("Current URL:", page.url, file=sys.stderr)
        print("Title:", page.title(), file=sys.stderr)
        print(
            "Prose count:",
            page.locator("div.prose.max-w-none").count(),
            file=sys.stderr,
        )

        lesson_body = page.locator("div.prose.max-w-none")
        try:
            lesson_body.wait_for(
                state="visible",
                timeout=NAVIGATION_TIMEOUT_MS,
            )
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(
                "The dynamically mounted lesson body did not load."
            ) from exc

        title = page.locator("h1")
        try:
            title.wait_for(
                state="visible",
                timeout=NAVIGATION_TIMEOUT_MS,
            )
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(
                "The lesson title did not load."
            ) from exc

        soup = BeautifulSoup(lesson_body.inner_html(), "html.parser")

        chrome_terms = (
            "navigation",
            "sidebar",
            "assignment",
            "revision",
            "header",
            "footer",
            "page-chrome",
        )

        removable_tags = {
            "nav",
            "aside",
            "header",
            "footer",
            "script",
            "style",
            "noscript",
        }

        allowed_attributes = {
            "a": {"href", "title"},
            "img": {"src", "alt", "title", "width", "height"},
            "iframe": {
                "src",
                "srcdoc",
                "title",
                "allow",
                "allowfullscreen",
                "loading",
            },
            "td": {"colspan", "rowspan", "scope"},
            "th": {"colspan", "rowspan", "scope"},
            "code": {"class"},
        }

        for element in soup.find_all(True):
            attrs = element.attrs or {}

            metadata = " ".join(
                str(value)
                for name, value in attrs.items()
                if name == "id"
                or name == "class"
                or name.startswith("data-")
            ).lower()

            if element.name in removable_tags or any(
                term in metadata for term in chrome_terms
            ):
                element.decompose()
                continue

            permitted = allowed_attributes.get(element.name, set())

            element.attrs = attrs

            for attribute in list(attrs):
                if attribute not in permitted:
                    del attrs[attribute]

        clean_title = " ".join(title.inner_text().split())
        if not clean_title:
            raise RuntimeError("Kalvium returned an empty lesson title.")

        title_tag = soup.new_tag("h1")
        title_tag.string = clean_title
        soup.insert(0, title_tag)

        html = str(soup).strip()
        if not html or html == f"<h1>{clean_title}</h1>":
            raise RuntimeError("Kalvium returned an empty lesson body.")

        return html