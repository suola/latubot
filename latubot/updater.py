"""Status updater using backend python api."""
import logging
import json

import tweeter

from source import api

logger = logging.getLogger(__name__)
dumps = json.dumps


def do_update(sports=None, areas=None, since='8M'):
    """Update main function."""
    sports = sports or ('latu',)
    areas = areas or ('oulu',)

    for sport in sports:
        for area in areas:
            do_update_area_sport(sport, area, since)


def do_update_area_sport(sport, area, since):
    """Update specific, sport, area combo."""
    try:
        data = api.get_area(sport, area, since=since)
    except ValueError as e:
        logger.error(e)
        return

    twitter_api_keys = get_twitter_api_keys(sport, area)
    twitter_api = tweeter.get_api(twitter_api_keys)

    for city in data:
        for city, update in data[city].items():
            # msg = f'({area.capitalize()}) {city}, {update}'
            msg = f'{city}, {update}'
            tweeter.send(twitter_api, msg)


def get_twitter_api_keys(sport, area):
    return tweeter.TwitterKeys(
            'R5mzDvQJBMrghDWZw9YgiiZaY',
            'x7smT9MptfWo1jTXm2qf3cx7I5HDWSMlRnn3yfXM7aMfrQamTw',
            '832683766485131265-TvOImKLaB7F9wwV6308r5shGnyfQjEJ',
            '2MrMhQibRvXRDEr2LvxTPpLc6WUCgab6HsBMByueZTDUJ',
            )


if __name__ == "__main__":
    do_update()
