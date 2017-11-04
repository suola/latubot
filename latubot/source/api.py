"""API for latubot

- sport (latu, luistelu)
- area (OULU, SYOTE)
- city (oulu, haukipudas)
- place ("Iinatti 8km"...)

"""

from latubot.source import kunto
from latubot.source import time_utils


def sport_names():
    """Supported sport names."""
    return kunto.ALL_SPORTS


def area_names():
    """Supported area names."""
    return kunto.ALL_AREAS


def load(sport, area, raw_response=False, since=None, empty=False):
    sport = sport.lower()
    if sport not in sport_names():
        raise ValueError(f'Invalid sport {sport}')

    area = area.upper()
    if area not in area_names():
        raise ValueError(f'Invalid area {area}')

    # if new raw data sources are added, unify and combine data here
    data = kunto.load(sport, area)

    if raw_response:
        return data

    if since:
        data = _filter_data(data, _time_filter(since))

    # empty=True to include empty items as well
    if not empty:
        data = _remove_empty(data)

    return data


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
        return all_ or 'date' in v
    return f


def _time_filter(since):
    mins = time_utils.since_to_mins(since)

    def f(v):
        try:
            return time_utils.is_within(v['date'], mins)
        except KeyError:
            return False
    return f
