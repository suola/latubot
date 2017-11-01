"""Configuration mgmt.

BASE = "https://kunto.softroi.fi/LATU{area}/"
STATUS_LATU = BASE + "latuui/loadLatuStatusListAccordion.html"
STATUS_LUISTELU = BASE + "latuui/loadLuisteluStatusListAccordion.html"
LATEST = BASE + "latuui/loadLatuNewMarks.html"
MESSAGES = BASE + "latuui/loadLatuInfoMessageList.html"
IDS = BASE + "data/oulu/latu2shpid.json"
GML = BASE + "data/oulu/ladut.gml"
# Script urls for other resources were found
ACCORDION_SCRIPT = BASE + "script/frLatuMapAccordion.jsp"

"""

import os
import re
import logging


DEFAULT_AREA = 'OULU'
DEFAULT_SPORT = 'latu'

# Date format used internally
DATE_FMT = '%Y-%m-%d %H:%M'

# Minutes that must pass before tweeting a new update - this is to skip too
# frequent updates that sometimes occur (e.g. updated every 2 mins for 5 times
# in a row
MIN_MINS_BETWEEN_UPDATES = 30

# Sleep a while after each sent tweet to avoid spamming
SECS_TO_SLEEP_AFTER_TWEET = 10


# all areas that use SOFTROI kunto service
_ALL_AREAS = (
    'OULU', 'SYOTE', 'SOTKAMOVUOKATTI', 'KOLI', 'YLIVIESKA', 'TORNIO',
    'PIEKSAMAKI', 'KUOPIO', 'KAJAANI', 'HAMEENLINNA', 'KIRKKONUMMI',
    'VARKAUS', 'HYVINKAA', 'NIVALA', 'RAASEPORI', 'KUUSAMO')


# _SUPPORTED_AREAS = _ALL_AREAS
_SUPPORTED_AREAS = ('OULU', 'SYOTE')

_ALL_SPORTS = ('latu', 'luistelu')

logger = logging.getLogger(__name__)


def load():
    """Load app settings."""
    assert set(_SUPPORTED_AREAS) <= set(_ALL_AREAS)
    cfg = {
        'baseurl': "https://kunto.softroi.fi/LATU{area}/",
        'sports': {
            'latu': {
                "areas": _SUPPORTED_AREAS,
                "url": "latuui/loadLatuStatusListAccordion.html",
                'html_parser_opts': {
                    'acc_label': 'accordion',
                    },
                },
            'luistelu': {
                "areas": _SUPPORTED_AREAS,
                "url": "latuui/loadLuisteluStatusListAccordion.html",
                'html_parser_opts': {
                    'acc_label': 'accordion2',
                    }
                },
            },
        }

    return cfg


def get_twitter_api_keys(sport: str, area: str):
    """Load twitter api keys.

    API keys for twitter account for a sport + area must be defined in an
    environment variable. E.g. keys for latu updates in oulu must be defined in
    env var LATUBOT_KEYS_LATU_OULU.

    The value of the env var must contain 4 values separated by whitespace:
      consumer_key consumer_secret access_key access_secret
    """
    key = f'LATUBOT_KEYS_{sport.upper()}_{area.upper()}'
    try:
        return os.environ[key].split()
    except KeyError:
        logger.debug(f'No twitter keys for {sport}, {area}')
        return None


def get_configured():
    """Generator for configured (sport, area) tuples."""
    ks = (k for k in os.environ.keys() if k.startswith('LATUBOT_KEYS_'))
    for key in ks:
        m = re.match('LATUBOT_KEYS_(?P<sport>\w*)_(?P<area>\w*)', key)
        assert m
        yield m.group('sport'), m.group('area')


def url(c: dict, area: str, sport: str):
    return c['baseurl'].format(area=area) + c['sports'][sport]['url']
