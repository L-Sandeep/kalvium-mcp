"""Attendance data extraction for Kalvium."""

import json
from typing import Any

from auth import open_browser


def _extract_rsc_object(html: str, key: str) -> dict[str, Any]:
    """Extract a JSON object embedded in a Next.js RSC payload."""

    marker = f'\\"{key}\\":'
    start = html.find(marker)

    if start == -1:
        raise RuntimeError(f"Could not find '{key}' in Kalvium page data.")

    object_start = start + len(marker)
    raw = html[object_start:]
    decoded = raw.replace('\\"', '"')

    decoder = json.JSONDecoder()

    try:
        value, _ = decoder.raw_decode(decoded)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Could not decode '{key}' from Kalvium RSC data."
        ) from exc

    if not isinstance(value, dict):
        raise RuntimeError(f"Expected '{key}' to contain an object.")

    return value


def get_attendance(
    semester: int | None = None,
    month: int | None = None,
    year: int | None = None,
) -> dict[str, Any]:
    """Get Kalvium attendance, optionally filtered by semester and month."""

    url = "https://app.kalvium.community/attendance-hub"

    params = []

    if month is not None:
        if not 1 <= month <= 12:
            raise ValueError("month must be between 1 and 12.")

        if year is None:
            raise ValueError("year is required when month is specified.")

        params.append(f"date={year:04d}-{month:02d}-01")

    if semester is not None:
        params.append(f"semester={semester}")

    if params:
        url += "?" + "&".join(params)

    with open_browser() as (_, page):
        page.goto(url, wait_until="networkidle")
        html = page.content()

    monthly_data = _extract_rsc_object(html, "monthlyData")
    subject_data = _extract_rsc_object(html, "subjectWiseAttendance")

    return {
        "month": monthly_data.get("month"),
        "overview": monthly_data.get("overview", {}),
        "subjects": subject_data.get("subjects", []),
        "selected_semester": subject_data.get("selectedSemester"),
        "current_semester": subject_data.get("currentSemester"),
        "available_semesters": subject_data.get("semesters", []),
    }