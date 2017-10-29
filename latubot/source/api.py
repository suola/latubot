"""API for latubot

- sport (latu, luistelu)
- area (OULU, SYOTE)
- city (oulu, haukipudas)
- place ("Iinatti 8km"...)

"""

from datetime import datetime

from . import raw
from . import time_utils


def get_area(sport, area, raw_response=False, since=None, empty=False):
    sport = sport.lower()
    if sport not in raw.sport_names():
        raise ValueError(f'Invalid sport {sport}')

    area = area.upper()
    if area not in raw.area_names():
        raise ValueError(f'Invalid area {area}')

    data = raw.load_area(area, sport)

    if raw_response:
        return data

    # From now only interested in parsed date, raw is dropped
    dates = _pick_dates(data)

    if since:
        dates = _filter_data(dates, _time_filter(since))

    # empty=True to include empty items as well
    if not empty:
        dates = _remove_empty(dates)

    return dates


def _pick_dates(data):
    return {a: {k: v.get('_date') for k, v in d.items()}
            for a, d in data.items()}


def _filter_data(data, f):
    nd = {a: {k: v for k, v in d.items() if f(v)} for a, d in data.items()}
    return nd


def _remove_empty(data):
    """Remove 1st empty places, then cities."""
    r = {a: {k: v for k, v in d.items() if v} for a, d in data.items()}
    r = {a: d for a, d in r.items() if d}
    return r


def _basic_filter(all_):
    """If all_=True include all items, otherwise only ones with date."""
    def f(v):
        return all_ or '_date' in v
    return f


def _time_filter(since):
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

    def f(v):
        if v is None:
            return False
        else:
            dt = datetime.strptime(v, raw.DATE_FMT)
            return time_utils.is_within(dt, mins)
    return f
