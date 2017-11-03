import re
from datetime import datetime, timedelta
import json


def is_within(td: datetime, mins: int):
    """is td within mins minutes from now?"""
    assert mins >= 0
    td_ref = datetime.now() - timedelta(minutes=mins)
    return td > td_ref


def get_date(s):
    """Get date from s, None if fails."""
    # In regular updates there is a colon, in latest updates -list there isn't
    m = re.match('Kunnostettu(:)? (.*)', s)
    if m and len(m.groups()) == 2:
        date_str = m.group(2)
    else:
        return None

    # str -> datetime
    _fmt = '%d.%m. klo %H:%M'
    try:
        date = datetime.strptime(date_str, _fmt)
    except ValueError:
        return None

    # guess the missing year
    now = datetime.now()
    new_date = date.replace(year=now.year)
    if new_date > now:
        new_date = date.replace(year=now.year-1)
    return new_date


def since_to_mins(since):
    if since.endswith('m'):
        mins = int(since[:-1])
    elif since.endswith('h'):
        mins = 60 * int(since[:-1])
    elif since.endswith('d'):
        mins = 24*60 * int(since[:-1])
    elif since.endswith('M'):
        mins = 31*24*60 * int(since[:-1])
    else:
        mins = int(since)

    return mins


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)
