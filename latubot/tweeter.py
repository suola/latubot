"""Send msg on twitter."""

import sys
from collections import namedtuple
import time
import logging

import tweepy

from . import cfg


# Twitter keys
TwitterKeys = namedtuple(
        'TwitterKeys',
        'consumer_key consumer_secret access_key access_secret')

logger = logging.getLogger(__name__)


def get_api(keys: TwitterKeys):
    """Get tweepy api."""
    auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
    auth.set_access_token(keys.access_key, keys.access_secret)
    api = tweepy.API(
            auth,
            wait_on_rate_limit=True,
            wait_on_rate_limit_notify=True
            )
    logger.debug('Authenticated w/ twitter API')
    return api


def get_my_updates(api: tweepy.API, count: int=50):
    """Get last count my updates."""
    return api.user_timeline(count=count)


def send(api: tweepy.API, msg: str):
    """Send tweet w/ authenticated api."""
    if api is None:
        print(f'tweet: {msg}')
    else:
        api.update_status(msg)
        time.sleep(cfg.SECS_TO_SLEEP_AFTER_TWEET)


def keys_from_str(s: str):
    """Whitespace separated string "cons_key cons_sec acc_key acc_sec"."""
    return TwitterKeys(*s.split())


if __name__ == "__main__":
    keys = TwitterKeys(1, 2, 3, 4)
    api = get_api(keys)
    if len(sys.argv) > 1:
        # print(sys.argv[1])
        send(api, sys.argv[1])
    else:
        # Ask for msg, tweet it
        msg = input('msg> ')
        send(api, msg)
