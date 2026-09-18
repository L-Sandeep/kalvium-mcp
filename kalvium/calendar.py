"""Schedule data extraction for Kalvium."""

import re
from datetime import datetime, timezone
from typing import Any

from auth import open_browser


TIME_RANGE_PATTERN = re.compile(
    r"^\d{1,2}:\d{2}\s+(AM|PM)\s+-\s+\d{1,2}:\d{2}\s+(AM|PM)$"
)


def get_schedule() -> dict[str, Any]:
    """Get the current week's Kalvium class schedule."""

    url = "https://app.kalvium.community/calendar"

    with open_browser() as (_, page):
        page.goto(url, wait_until="networkidle")

        times = page.locator("time")
        events = []

        for i in range(times.count()):
            time_element = times.nth(i)
            time_text = time_element.inner_text().strip()

            if not TIME_RANGE_PATTERN.match(time_text):
                continue

            datetime_attribute = time_element.get_attribute("datetime")

            if not datetime_attribute:
                continue

            # The datetime attribute contains:
            # "2026-09-15T04:00:00.000Z - 2026-09-15T04:45:00.000Z"
            start_datetime_text = datetime_attribute.split(" - ", 1)[0]

            try:
                start_datetime = datetime.fromisoformat(
                    start_datetime_text.replace("Z", "+00:00")
                )
            except ValueError:
                continue

            # Kalvium stores the timestamp in UTC.
            # Convert it to the local timezone used by the browser.
            local_datetime = start_datetime.astimezone()

            container = time_element.locator("..").locator("..")
            text = container.inner_text().strip()

            lines = [line.strip() for line in text.splitlines() if line.strip()]

            if len(lines) < 2:
                continue

            subject = lines[1]

            events.append(
                {
                    "date": local_datetime.date().isoformat(),
                    "day": local_datetime.strftime("%A"),
                    "time": time_text,
                    "subject": subject,
                }
            )

        body_text = page.locator("body").inner_text()

    date_matches = re.findall(
        r"(Sun|Mon|Tue|Wed|Thu|Fri|Sat)\s+(\d{1,2}\s+\w+\s+\d{4})",
        body_text,
    )

    dates = [
        {
            "day": day,
            "date": date,
        }
        for day, date in date_matches
    ]

    return {
        "week": dates,
        "events": events,
        "event_count": len(events),
    }