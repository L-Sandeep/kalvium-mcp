"""Assessment data extraction for Kalvium."""

import json
from typing import Any

from auth import open_browser


def _extract_rsc_value(html: str, key: str) -> Any:
    """Extract a JSON value embedded in Kalvium's Next.js RSC payload."""

    marker = f'\\"{key}\\":'
    start = html.find(marker)

    if start == -1:
        raise RuntimeError(f"Could not find '{key}' in Kalvium page data.")

    value_start = start + len(marker)
    raw = html[value_start:]
    decoded = raw.replace('\\"', '"')

    decoder = json.JSONDecoder()

    try:
        value, _ = decoder.raw_decode(decoded)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Could not decode '{key}' from Kalvium RSC data."
        ) from exc

    return value


def get_assessments() -> dict[str, Any]:
    """Get scheduled and completed assessments from Kalvium."""

    url = "https://app.kalvium.community/assessment-corner"

    with open_browser() as (_, page):
        page.goto(url, wait_until="networkidle")
        html = page.content()

    scheduled = _extract_rsc_value(html, "assessments")
    completed = _extract_rsc_value(html, "initialResult")

    if not isinstance(scheduled, list):
        raise RuntimeError("Expected 'assessments' to be a list.")

    if not isinstance(completed, dict):
        raise RuntimeError("Expected 'initialResult' to be an object.")

    return {
        "scheduled": scheduled,
        "completed": completed.get("docs", []),
    }