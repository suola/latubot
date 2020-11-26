"""Tweet updates

- Build tweet message from an update
- Authenticate correct twitter api based on update location
- Send tweet
"""

import logging
import functools
import time
from collections import namedtuple

import tweepy
import dateutil.tz

from latubot import cfg
from latubot.update import load_location

logger = logging.getLogger(__name__)
tz_local = dateutil.tz.gettz("Europe/Helsinki")

# Twitter keys
TwitterKeys = namedtuple(
    "TwitterKeys", "consumer_key consumer_secret access_key access_secret"
)


def tweet_update(update):
    """Send tweet for the update."""
    location = load_location(update["location"])
    keys = cfg.get_twitter_api_keys(location["type"], location["area"])
    if keys is None:
        return None

    twitter_api_keys = TwitterKeys(*keys)
    api = _get_api(twitter_api_keys)
    if api is None:
        return

    msg = _build_tweet_msg(location, update)
    _send(api, msg)


def _send(api: tweepy.API, msg: str):
    """Send tweet w/ authenticated api."""
    if api is None:
        logger.info(f"tweet: {msg}")
    else:
        api.update_status(msg)
        time.sleep(cfg.SECS_TO_SLEEP_AFTER_TWEET)


def _build_tweet_msg(location, update):
    """Build tweet message for the update."""
    group = location["group"]
    name = location["name"]
    date = update["date"].astimezone(tz_local).strftime("%d.%m klo %H:%M")
    msg = f"{group}, {name}; Kunnostettu {date}"
    msg = _add_hashtags(msg, location["area"])
    return msg


def _add_hashtags(msg: str, area: str, max_length: int = 140):
    """Add hashtags if length allows."""
    tags = ("#hiihto", f"#{area.lower()}")
    for tag in tags:
        if len(msg) + len(tag) + 1 <= max_length:
            msg = " ".join((msg, tag))

    return msg[:max_length]


@functools.lru_cache
def _get_api(keys):
    """Get tweepy api for keys."""
    auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
    auth.set_access_token(keys.access_key, keys.access_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    logger.debug("Authenticated w/ twitter API")
    return api
