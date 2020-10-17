from datetime import datetime
import json

import dateutil.tz

fin_tz = dateutil.tz.gettz("Europe/Helsinki")


def now_tz():
    now = datetime.now(fin_tz)
    now_naive = now.replace(tzinfo=None)
    return now_naive


def since_to_delta(since):
    """Convert since to timedelta."""
    unit_map = {
        "m": "minutes",
        "h": "hours",
        "d": "days",
        "M": "months",
        "y": "years",
    }
    v, unit = since[:-1], since[-1]
    kwargs = {unit_map[unit]: int(v)}
    return dateutil.relativedelta.relativedelta(**kwargs)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)
