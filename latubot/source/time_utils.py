from datetime import datetime, timedelta
import json


def is_within(td: datetime, mins: int):
    """is td within mins minutes from now?"""
    assert mins >= 0
    td_ref = datetime.now() - timedelta(minutes=mins)
    return td > td_ref


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
