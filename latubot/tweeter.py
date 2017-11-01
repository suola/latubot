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


def get_my_updates(api, count=50):
    """Get last count my updates."""
    return api.user_timeline(count=count)


def send(api, msg):
    """Send tweet w/ authenticated api."""
    msg = add_hashtags(msg, area)
    if api is None:
        print(f'tweet: {msg}')
    else:
        api.update_status(msg)
        time.sleep(cfg.SECS_TO_SLEEP_AFTER_TWEET)


def add_hashtags(msg, area, max_length=140):
    """Add hashtags if length allows."""
    tags = ('#hiihto', f'#{area.lower()}')
    for tag in tags:
        if len(msg) + len(tag) + 1 <= max_length:
            msg = ' '.join((msg, tag))

    return msg[:max_length]


def keys_from_str(s):
    """Whitespace separated string "cons_key cons_sec acc_key acc_sec"."""
    return TwitterKeys(s.split())


if __name__ == "__main__":
    keys = TwitterKeys(1, 2, 3, 4)
    api = get_api(keys)
    if len(sys.argv) > 1:
        # print(sys.argv[1])
        send(sys.argv[1])
    else:
        # Ask for msg, tweet it
        msg = input('msg> ')
        send(msg)
