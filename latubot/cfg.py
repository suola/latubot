"""Configuration mgmt.
"""

import os
import re
import logging


# Minutes that must pass before tweeting a new update - this is to skip too
# frequent updates that sometimes occur (e.g. updated every 2 mins for 5 times
# in a row
MIN_MINS_BETWEEN_UPDATES = 30

# Sleep a while after each sent tweet to avoid spamming
SECS_TO_SLEEP_AFTER_TWEET = 10


logger = logging.getLogger(__name__)


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
