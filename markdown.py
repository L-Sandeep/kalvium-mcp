"""HTML-to-Markdown conversion utilities."""

from markdownify import markdownify


def html_to_markdown(html: str) -> str:
    """Convert lesson HTML into clean GitHub-flavoured Markdown.

    Args:
        html: HTML fragment returned by :func:`scraper.get_lesson`.

    Returns:
        The equivalent Markdown with ATX headings and fenced code blocks.
    """
    if not html.strip():
        raise ValueError("Cannot convert empty HTML to Markdown.")

    return markdownify(html, heading_style="ATX", code_language="").strip()
