from datetime import datetime


def format_dt(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")
