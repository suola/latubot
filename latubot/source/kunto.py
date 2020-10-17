"""Fetch and parse data from fluentprogress (previously kunto) servers."""

import logging
import json

import requests
import dateutil.parser

from latubot import time_utils

logger = logging.getLogger(__name__)


# all areas with kunto service
ALL_AREAS = (
    "HAMEENLINNA",
    "HYRYNSALMIPUOLANKA",
    "HYVINKAA",
    "IISALMI",
    "KAJAANI",
    "KEMI",
    "KIRKKONUMMI",
    "KOLI",
    "KOUVOLA",
    "KUHMO",
    "KUOPIO",
    "KUUSAMO",
    "MANTSALA",
    "MIKKELI",
    "NIVALA",
    "OULU",
    "PIEKSAMAKI",
    "RAASEPORI",
    "SUOMUSSALMI",
    "SOTKAMOVUOKATTI",
    "SYOTE",
    "TORNIO",
    "VARKAUS",
    "YLIVIESKA",
)

ALL_SPORTS = ("latu", "luistelu")

_DEFAULT_AREA = "OULU"
_DEFAULT_SPORT = "latu"
_URL_TEMPLATE = "https://{area}.fluentprogress.fi/outdoors/"


def load(sport: str = _DEFAULT_SPORT, area: str = _DEFAULT_AREA, fn=None):
    """Load data for (sport, area) combo."""
    if sport not in ALL_SPORTS:
        raise ValueError(f"invalid sport {sport!r}")

    if area not in ALL_AREAS:
        raise ValueError(f"invalid area {area!r}")

    if fn:
        logger.debug(f"Load updates from {fn}")
        raw = open(fn).read()
    else:
        raw = _load_raw_data(area)

    updates = _parse(raw, sport)

    _log_updates(updates)
    return updates


def _load_raw_data(area):
    """Load raw data from kunto server."""
    base_url = _URL_TEMPLATE.format(area=area.lower())
    url = base_url + "api/venues"
    resp = requests.get(url)
    resp.encoding = "utf-8"
    return resp.text


def _parse(txt, sport):
    """Parse server response for updates on sport.

    txt: {
        "type": "FeatureCollection",
        "features": [
            {
                "id": <int>,
                "type": <str>, ("skitrack", "skatefield", ...)
                "group": <str>, ("Oulunsalo", "Kempele", ...)
                "name": <str>, ("Kirkonkylän kenttä", ...)
                "description": <str>, (free text)
                "status": <str>, ("CLOSED", "OPEN", "BAD CONDITION"...) (check spelling)
                "images": [<int>], (?)
                "maintainedAt": <str> ("2020-03-20T06:50:54.031+02:00")
            },
            ...
        }
    }
    """
    sport_map = {"latu": "skitrack", "luistelu": "skatefield"}
    d = json.loads(txt)
    updates = (f["properties"] for f in d["features"])
    sport_updates = [v for v in updates if v["type"] == sport_map[sport]]

    for v in sport_updates:
        v["date"] = _parse_maintained_at(v.get("maintainedAt"))

    return sport_updates


def _parse_maintained_at(v):
    """Parse maintainedAt value from an update."""
    try:
        return dateutil.parser.isoparse(v)
    except Exception as e:
        if v:
            logger.error(f"Can't parse date from {v!r} ({e})")
        return None


def _log_updates(updates):
    """Log updates."""
    n = len(updates)
    n_with_date = sum(1 for v in updates if v["date"])
    logger.info(f"Loaded {n} items ({n_with_date} w/ date)")


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.DEBUG)
    fn = sys.argv[1] if len(sys.argv) > 1 else None
    d1 = load(sport="latu", fn=fn)
    print(json.dumps(d1, cls=time_utils.DateTimeEncoder, indent=2))
