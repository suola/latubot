import logging
import json

import requests

import tweeter


logger = logging.getLogger(__name__)
dumps = json.dumps


def do_update(sports=None, areas=None, since='8M', url=None):
    """Update main function."""
    sports = sports or ('latu',)
    areas = areas or ('oulu',)
    url = url or 'http://localhost:5000/v1'

    for sport in sports:
        for area in areas:
            do_update_area_sport(sport, area, since, url)


def do_update_area_sport(sport, area, since, base_url):
    """Update specific, sport, area combo."""
    url = '/'.join((base_url, f'{sport}/{area}/'))
    if since:
        url += f'?since={since}'

    resp = requests.get(url)

    if resp.status_code != 200:
        logger.error(resp.text)
        return

    data = resp.json()
    # print(dumps(data))
    # return

    twitter_api_keys = get_twitter_api_keys(sport, area)
    twitter_api = tweeter.get_api(twitter_api_keys)

    for city in data:
        for city, update in data[city].items():
            tweeter.send(twitter_api, f'{city}: {update}')


def get_twitter_api_keys(sport, area):
    return tweeter.TwitterKeys(
            'R5mzDvQJBMrghDWZw9YgiiZaY',
            'x7smT9MptfWo1jTXm2qf3cx7I5HDWSMlRnn3yfXM7aMfrQamTw',
            '832683766485131265-TvOImKLaB7F9wwV6308r5shGnyfQjEJ',
            '2MrMhQibRvXRDEr2LvxTPpLc6WUCgab6HsBMByueZTDUJ',
            )


if __name__ == "__main__":
    do_update()
