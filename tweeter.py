#!/usr/bin/env python3
"""Twitter bot latutilanteen raportointiin
"""

import sys
import tweepy
from collections import namedtuple

import settings


# Twitter keys
TwitterKeys = namedtuple(
        'TwitterKeys',
        'consumer_key consumer_secret access_key access_secret')


# API to twitter, modified only in _authenticate(), read only in _get_api()
_twitter_api = None


def _get_cfg():
    """read twitter config from settings."""
    try:
        tc = TwitterKeys(
                settings.cfg['TWITTER_CONSUMER_KEY'],
                settings.cfg['TWITTER_CONSUMER_SECRET'],
                settings.cfg['TWITTER_ACCESS_KEY'],
                settings.cfg['TWITTER_ACCESS_SECRET'])
    except KeyError as e:
        sys.exit('Missing config var "%s"?' % e)

    return tc


def _authenticate():
    """Authenticate w/ Twitter API."""
    global _twitter_api

    if _twitter_api is not None:
        return

    # Read twitter config
    tc = _get_cfg()

    auth = tweepy.OAuthHandler(tc.consumer_key, tc.consumer_secret)
    auth.set_access_token(tc.access_key, tc.access_secret)
    _twitter_api = tweepy.API(auth)

    print('Authenticated w/ twitter API')


def _get_api():
    _authenticate()
    return _twitter_api


def send(msg):
    api = _get_api()
    api.update_status(msg)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Ask for msg, tweet cmd line
        # print(sys.argv[1])
        send(sys.argv[1])
    else:
        # Ask for msg, tweet it
        msg = input('msg> ')
        send(msg)
