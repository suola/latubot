"""Status updater using backend python api."""

import logging
import json
import datetime

from latubot import cfg
from latubot import tweeter
from latubot.source import api, time_utils

logger = logging.getLogger(__name__)
dumps = json.dumps


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
        sports = sports or cfg._ALL_SPORTS
        areas = areas or cfg._ALL_AREAS
        for sport in sports:
            for area in areas:
                print(f" {sport} - {area}")
                do_update_area_sport(sport, area, since, dry_run)


def do_update_area_sport(sport, area, since, dry_run=False):
    """Update sport, area combo."""
    try:
        data = api.get_area(sport, area, since=since)
    except ValueError as e:
        logger.error(e)
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
        for city, place in data[city].items():
            msg = f"{city}; {place['txt']}"
            msg = add_hashtags(msg, area)
            if should_send_update(my_tweets, msg, city):
                tweeter.send(twitter_api, msg)


def add_hashtags(msg, area, max_length=140):
    """Add hashtags if length allows."""
    tags = ('#hiihto', f'#{area.lower()}')
    for tag in tags:
        if len(msg) + len(tag) + 1 <= max_length:
            msg = ' '.join((msg, tag))

    return msg


def should_send_update(my_tweets, msg, city):
    """Whether should send update or not?."""
    if my_tweets is None:
        return True

    now = datetime.datetime.utcnow()
    min_age = datetime.timedelta(minutes=cfg.MIN_MINS_BETWEEN_UPDATES)

    for update in my_tweets:
        if update.text == msg:
            logger.info(f"'{msg}' already tweeted at {update.created_at}")
            return False
        elif update.text.startswith(city):
            # ix is dependent on the tweet message syntax
            ix = len(city) + len('; ')
            utext = update.text[ix:]

            # skip if tweeted about this place too recently
            utext_without_tags = utext.split('#', 1)[0].strip()
            update_date = time_utils.get_date(utext_without_tags)
            age = now - update_date
            # age = delta.seconds / 60
            if age < min_age:
                logger.info(f"{msg} - {age} (< {min_age}) mins "
                            "since prev update, skip")
                return False
            else:
                logger.info(f"{msg} - {age} (>= {min_age}) mins "
                            "since prev update")

    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # do_update(since='24h', areas=('OULU',), dry_run=False)
    do_update(since='24h', dry_run=False)
