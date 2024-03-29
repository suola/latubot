"""Tweet updates

- Build tweet message from an update
- Authenticate correct twitter api based on update location
- Send tweet
"""

import logging
import functools
import time
import random
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


def tweet_update(update, pretend):
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
    return _send(None if pretend else api, msg)


def _send(api: tweepy.API, msg: str):
    """Send tweet w/ authenticated api."""
    if api is None:
        logger.info(f"pretend tweet: {msg}")
        return True
    else:
        logger.debug(f"send tweet: {msg}")
        try:
            api.update_status(msg)
        except tweepy.TweepError as e:
            logger.error(f"error {e} sending tweet: {msg}")
            return False
        else:
            time.sleep(cfg.SECS_TO_SLEEP_AFTER_TWEET)
            return True


def _build_tweet_msg(location, update, max_length=280):
    """Build tweet message for the update."""
    group = location["group"]
    name = location["name"]
    date = update["date"].astimezone(tz_local).strftime("%d.%m klo %H:%M")
    description = update.get("description")
    is_closed = update.get("status", "").upper() == "CLOSED"
    action = "Päivitetty" if is_closed else "Kunnostettu"

    msg = f"{group}, {name}; {action} {date}"

    # Add description if it exists and fits
    if description:
        msg_ = f"{msg} ({description})"
        if len(msg_) <= max_length:
            msg = msg_

    msg = _add_hashtags(msg, location["area"], max_length)
    return msg


def _add_hashtags(msg: str, area: str, max_length: int = 140):
    """Add hashtags if length allows."""
    tags = (("#hiihto", 0.01), (f"#{area.lower()}", 1))
    for tag, probability in tags:
        if len(msg) + len(tag) + 1 <= max_length and random.random() < probability:
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
