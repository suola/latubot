"""Send msg on twitter."""

import sys
import re
from collections import namedtuple
from datetime import datetime
import time
import logging

import tweepy
import pytz

from latubot import cfg


# Twitter keys
TwitterKeys = namedtuple(
    "TwitterKeys", "consumer_key consumer_secret access_key access_secret"
)

logger = logging.getLogger(__name__)


def get_api(keys: TwitterKeys):
    """Get tweepy api."""
    auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
    auth.set_access_token(keys.access_key, keys.access_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    logger.debug("Authenticated w/ twitter API")
    return api


def get_my_updates(api: tweepy.API, count: int = 50):
    """Get last count my updates."""
    return api.user_timeline(count=count)


def send(api: tweepy.API, msg: str):
    """Send tweet w/ authenticated api."""
    if api is None:
        print(f"tweet: {msg}")
    else:
        api.update_status(msg)
        time.sleep(cfg.SECS_TO_SLEEP_AFTER_TWEET)


def keys_from_str(s: str):
    """Whitespace separated string "cons_key cons_sec acc_key acc_sec"."""
    return TwitterKeys(*s.split())


def parse_tweet(tweet: tweepy.Status):
    """Get data from tweet."""
    text = tweet.text
    sent = _utc_to_local(tweet.created_at)

    # Try to parse location and date of update from text
    m = re.match(cfg.TWEET_RE_PATTERN, text)
    if m:
        location, date_str, hashtags = m.groups()
        try:
            date = parse_dt(date_str)
        except ValueError as e:
            logger.warning("error (%s) parsing date from tweet %s", e, text)
        else:
            date = date.replace(year=sent.year)
            if date > sent:
                date = date.replace(year=sent.year - 1)
    else:
        logger.warning("error parsing tweet %s", text)
        location, date = None, None

    return text, sent, location, date


def _utc_to_local(naive_utc_dt):
    """Convert naive UTC time to naive localtime."""
    fin_tz = pytz.timezone("Europe/Helsinki")
    utc_dt = pytz.utc.localize(naive_utc_dt)
    localtime_dt = utc_dt.astimezone(fin_tz)
    naive_localtime_dt = localtime_dt.replace(tzinfo=None)
    return naive_localtime_dt


def parse_dt(date_str):
    """Parse datetime from date_str"""
    # Prepend current year into both date_str and string to handle
    # 29.02 on leap year - otherwise strptime assumes year 1900 and
    # fails
    fmt = f"%Y.{cfg.TWEET_TIME_FMT}"
    date_str = f"{datetime.now().year}.{date_str}"
    return datetime.strptime(date_str, fmt)


if __name__ == "__main__":
    # keys = TwitterKeys(1, 2, 3, 4)
    keys = TwitterKeys(*cfg.get_twitter_api_keys("latu", "OULU"))
    api = get_api(keys)
    tweets = get_my_updates(api)
    ptw = parse_tweet(tweets[0])
    if len(sys.argv) > 1:
        # print(sys.argv[1])
        send(api, sys.argv[1])
    else:
        # Ask for msg, tweet it
        msg = input("msg> ")
        send(api, msg)
