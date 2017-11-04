"""Status updater using backend python api."""

import logging
from datetime import datetime, timedelta

from latubot import cfg
from latubot import tweeter
from latubot.source import api, time_utils

logger = logging.getLogger(__name__)


def do_update_aws_lambda(event, context):
    """Entry point for AWS lambda function."""
    logger.debug("aws triggered by event %s" % event)
    do_update(since='15m')


def do_update(sports=None, areas=None, since='8M', dry_run=False):
    """Update main function."""
    if not dry_run:
        # Update all sport+area pairs w/ configuration
        def inc(x, xs):
            return xs is None or x.upper() in map(str.upper, xs)

        for sport, area in cfg.get_configured():
            logger.debug('got config for %s-%s', sport, area)
            if inc(sport, sports) and inc(area, areas):
                do_update_area_sport(sport, area, since)

    else:
        sports = sports or api.sport_names()
        areas = areas or api.area_names()
        for sport in sports:
            for area in areas:
                print(f" {sport} - {area}")
                do_update_area_sport(sport, area, since, dry_run)


def do_update_area_sport(sport, area, since, dry_run=False):
    """Update sport, area combo."""
    try:
        data = api.load(sport, area, since=since)
    except ValueError as e:
        logger.error(e)
        return

    if not data:
        logger.debug('no updates for %s - %s', sport, area)
        return

    if dry_run:
        twitter_api = None
        my_tweets = None
    else:
        twitter_api_keys = tweeter.TwitterKeys(
                *cfg.get_twitter_api_keys(sport, area))
        twitter_api = tweeter.get_api(twitter_api_keys)
        my_tweets = tweeter.get_my_updates(twitter_api, count=50)

    for city in data:
        for place, update in data[city].items():
            location = cfg.TWEET_LOCATION_FMT.format(city=city, place=place)
            if should_send_update(my_tweets, location, update):
                msg = get_tweet_msg(area, location, update)
                tweeter.send(twitter_api, msg)


def get_tweet_msg(area, location, update):
    if 'date' in update:
        date = datetime.strftime(update['date'], cfg.TWEET_TIME_FMT)
        msg = cfg.TWEET_FMT.format(location=location, date=date)
    else:
        msg = cfg.TWEET_FMT2.format(location=location, text=update['txt'])

    msg = add_hashtags(msg, area)

    return msg


def add_hashtags(msg: str, area: str, max_length: int=140):
    """Add hashtags if length allows."""
    tags = ('#hiihto', f'#{area.lower()}')
    for tag in tags:
        if len(msg) + len(tag) + 1 <= max_length:
            msg = ' '.join((msg, tag))

    return msg[:max_length]


def should_send_update(my_tweets, location, update):
    """Whether should send update or not?.

    Check when the last update about current location was tweeted,
    and if it was too recently, don't send this update.

    If updates were stored in a db, that should be used for this.
    """
    if my_tweets is None:
        return True

    try:
        update_dt = update['date']
    except KeyError:
        logger.warning(f'no timestamp in {update["txt"]}')
        update_dt = datetime.utcnow()

    min_age = timedelta(minutes=cfg.MIN_MINS_BETWEEN_UPDATES)

    # Find newest update for the same location, and parse time from
    # previous update from that. No need to look for older updates, latest
    # should have the newest update. (Assumption: TWEET_FMT starts with
    # location)
    for tweet in my_tweets:
        # don't use the following simple version for now, since in some
        # tweets format has been slightly different. Once format stabilizes,
        # can go back to simple version
        # if not tweet.text.startswith(location):
            # continue

        text, sent_dt, parsed_location, made_dt = tweeter.parse_tweet(tweet)

        if not parsed_location or parsed_location not in location:
            continue

        # unable to parse date from the tweet
        if made_dt is None:
            continue

        age = update_dt - made_dt
        logger.info(f"{location} '{update['txt']}' age {age}")
        return age > min_age

    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # do_update(since='24h', areas=('OULU',), dry_run=False)
    do_update(since='24h', dry_run=False)
