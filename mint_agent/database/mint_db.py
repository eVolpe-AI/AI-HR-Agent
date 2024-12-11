import os
from datetime import datetime

import pytz
from dotenv import load_dotenv


def to_db_time(timestamp, user_timezone: str, format="%Y-%m-%d %H:%M:%S"):
    load_dotenv()
    try:
        db_timezone = pytz.timezone("UTC")
        user_timezone = pytz.timezone(user_timezone)

        if not db_timezone:
            raise ValueError("DB_TIMEZONE must be set in .env file")

        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, format)

        timestamp = user_timezone.localize(timestamp)

        return timestamp.astimezone(db_timezone).strftime(format)
    except Exception as e:
        raise ValueError(f"Error converting time: {e}")
