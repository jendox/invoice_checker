from datetime import date


def parse_optional_date(value: str | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    cleaned = value.strip()
    if not cleaned:
        return None
    return date.fromisoformat(cleaned)
