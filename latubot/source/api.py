"""API for latubot

- sport (latu, luistelu)
- area (OULU, SYOTE)
- group (oulu, haukipudas) (previously city)
- name ("Iinatti 8km"...) (previously place)

"""

import logging
from datetime import datetime

from dateutil.tz import tzutc

from latubot.source import kunto
from latubot import time_utils

logger = logging.getLogger(__name__)


def sport_names():
    """Supported sport names."""
    return kunto.ALL_SPORTS


def area_names():
    """Supported area names."""
    return kunto.ALL_AREAS


def load(sport, area, since=None, fn=None):
    """Load updates."""
    sport = sport.lower()
    if sport not in sport_names():
        raise ValueError(f"Invalid sport {sport}")

    area = area.upper()
    if area not in area_names():
        raise ValueError(f"Invalid area {area}")

    # if new data sources are added, unify and combine data here
    data = kunto.load(sport, area, fn=fn)

    if since:
        data = filter(_time_filter(since), data)

    return list(data)


def _time_filter(since):
    """Filter function to pass only items w/ date not older than since."""
    delta = time_utils.since_to_delta(since)
    now = datetime.now(tzutc())

    def f(v):
        try:
            return v["date"] and now - delta < v["date"]
        except KeyError:
            return False

    return f


if __name__ == "__main__":
    import sys
    import json

    logging.basicConfig(level=logging.DEBUG)
    fn = sys.argv[1] if len(sys.argv) > 1 else None
    d1 = load(sport="latu", area="OULU", since="7M", fn=fn)
    logger.debug(f"Loaded {len(d1)} updates")
    print(json.dumps(d1, cls=time_utils.DateTimeEncoder, indent=2))
