#!/usr/bin/env python3
"""Twitter bot latutilanteen raportointiin
"""

import os
import os.path as op
import glob
import json
import datetime
import time
from pprint import pprint
import argparse
from collections import namedtuple

import requests
from lxml import html
from jsondiff import diff
import tweepy

import tweeter

# Configuration
DATA_URL = "https://kunto.softroi.fi/LATUOULU/latuui/" \
           "loadLatuStatusListAccordion.html"
# Seconds to wait between successive tweets from one update
SECS_BETWEEN_TWEETS = 15
# Seconds to sleep between updates
SECS_BETWEEN_UPDATES = 300
# Max number of tweets to send from one update.
MAX_TWEETS_PER_UPDATE = 30
# how many mins must've passed since the last update to notice
# update. This is to ignore the repeated updates just a few minutes apart
# that happen often
MIN_MINS_BETWEEN_UPDATES = 30

# Status update - txt is read from server, mins is the calculated number
# of minutes between this update and the previous one (None if previous
# update not found)
StatusUpdate = namedtuple('StatusUpdate', 'age txt')


def run_server(city_filter, tweet=False, use_json=False, tweet_1st_update=False,
               simulate=False):
    print('restarting bot')
    ndata = {}
    i_update = 0
    while True:
        i_update += 1
        print('update %d' % i_update, _time_to_fn())

        # Read old and new data
        try:
            odata, ndata = _get_old_and_new_data(ndata, simulate,
                                                 use_json, i_update)
        except EOFError as e:
            print(e)
            break

        # Find out diffs between old and new
        changes = _get_diff(odata, ndata, city_filter)
        _calculate_time_since_prev_update(changes, odata)

        # Report diffs
        if i_update == 1 and not tweet_1st_update:
            pass
        else:
            _tweet_changes(changes, tweet, simulate)

        # Sleep a while
        if not simulate:
            time.sleep(SECS_BETWEEN_UPDATES)


def _get_old_and_new_data(ndata, simulate, use_json, i_update):
    """Read old and new data."""
    if simulate:
        # Simulation mode for testing, reads files from data-dir
        odata, ndata = _get_old_and_new_data_simulate(i_update)
    elif use_json:
        # json-file mode, saves data in json-files and reads from them
        odata = _load_newest_json()
        ndata = load_data_from_server()
        _save_json(ndata)
    else:
        # Default mode, no data files created, status kept in memory
        odata = ndata
        ndata = load_data_from_server()

    return odata, ndata


def _get_old_and_new_data_simulate(i):
    """Get i'th and (i+1)'th oldest json files."""
    files = _read_json_file_listing()

    # Out of data files
    if i >= len(files):
        raise EOFError('no more data for simulation')

    ofn = files[i - 1]
    nfn = files[i]

    odata = _load_json(ofn)
    ndata = _load_json(nfn)

    return odata, ndata


def _get_diff(odata, ndata, city_filter):
    diffs = {}
    if odata and ndata:
        all_diffs = diff(odata, ndata)
        if all_diffs is not None:
            diffs = {city: all_diffs[city] for city in all_diffs
                     if not city_filter or city in city_filter}
        else:
            pprint(ndata)
    else:
        print('empty old or new data, ignoring diff')

    return diffs


def _calculate_time_since_prev_update(changes, odata):
    for city in changes:
        for k in changes[city]:
            mins = _calc_time_diff(odata[city][k], changes[city][k])
            print("{}: {}: {} mins since prev update".format(city, k, mins))
            # Replace status txt with StatusUpdate
            changes[city][k] = StatusUpdate(mins, changes[city][k])


def _tweet_changes(changes, send_tweets, simulate):
    i_change = 0
    for city in changes:
        for k, v in changes[city].items():
            msg = '{}, {}: {}'.format(city, k, v.txt)

            # Skip too frequent updates
            if v.age is not None and v.age < MIN_MINS_BETWEEN_UPDATES:
                print('{} - {} mins since prev update, skipping'.format(
                    msg, v.age))
                continue

            # Send or print msg
            if send_tweets:
                try:
                    print('tweeting', msg)
                    tweeter.send(msg)
                except tweepy.error.TweepError as e:
                    print('error tweeting: %s' % e)
            else:
                print('(not sending tweets): {}'.format(msg))

            # Quit if too many tweets sent to avoid spamming
            i_change += 1
            if i_change >= MAX_TWEETS_PER_UPDATE:
                print('%d tweets / update sent, skipping the rest' % i_change)

            # small interval between successive tweets
            if not simulate:
                time.sleep(SECS_BETWEEN_TWEETS)


def _save_json(data):
    if not op.exists('data'):
        os.makedirs('data')

    fn = 'data/{}.json'.format(_time_to_fn())
    print('save data in %s' % fn)
    with open(fn, 'w') as fid:
        json.dump(data, fid, indent=2)


def _read_json_file_listing():
    """Get list of json files, sorted from olders to newest."""
    if not op.exists('data'):
        os.makedirs('data')

    try:
        file_list = sorted(glob.glob('data/*.json'), key=op.getctime)
    except OSError as e:
        print('unable to read json file listing ({})'.format(e))
        file_list = {}

    return file_list


def _load_json(path):
    """Load json file from path."""
    print('load reference from %s' % path)
    with open(path) as fid:
        data = json.load(fid)

    return data


def _load_newest_json():
    json_files = _read_json_file_listing()
    if not json_files:
        return {}

    newest = json_files[-1]

    return _load_json(newest)


def load_data_from_server():
    r = _fetch_url(DATA_URL)
    data = _parse_html_source(html.fromstring(r.text))
    print('read and parsed new data from server')
    return data


def _fetch_url(url):
    # TODO: verify r.status_code == 200
    r = requests.get(url)
    return r


def _parse_html_source(tree):
    # Format
    # html.body.div.h3.a kaupunki
    # html.body.div.div<id="l_g9">.span[2].text name
    # html.body.div.div<id="l_g9">.ul.li.text status

    data = {}
    for city_list in tree.xpath('//*[@id="accordion"]/div'):
        city = city_list.xpath('preceding-sibling::h3[1]/a')[0].text
        data[city] = {}
        positions = city_list.xpath('div/span[2]')
        for pos in positions:
            statuses = pos.xpath('following-sibling::ul/li')
            strings = [x.text for x in statuses]
            status = ",".join(s.strip() for s in strings)
            data[city][pos.text] = status

    return data


def _time_to_fn():
    """get current timestamp in format usable for filename"""
    _fmt = '%Y-%m-%d-%H_%M_%S'
    now = datetime.datetime.now()
    return now.strftime(_fmt)


def _calc_time_diff(old, new):
    """Calculate difference (in minutes) between two time stamps."""
    # time string format
    _fmt = 'Kunnostettu: %d.%m. klo %H:%M'
    try:
        ndate = datetime.datetime.strptime(new, _fmt)
        odate = datetime.datetime.strptime(old, _fmt)
        date_diff = ndate - odate
        minutes = date_diff.days * 3600 + date_diff.seconds // 60
    except Exception as e:
        print('error calculating age: {}'.format(e))
        minutes = None

    return minutes


def print_cities():
    data = load_data_from_server()
    print('\n'.join(data.keys()))


def print_status(cities):
    data = load_data_from_server()
    if not cities:
        pprint(data)
    else:
        pprint({k: v for k, v in data.items() if k in cities})


def console_app():
    parser = argparse.ArgumentParser(description='Oulun alueen ladut')
    parser.add_argument('-l', '--list-cities', action='store_true',
                        help='kaupungit')
    parser.add_argument('-c', '--cities', default=None,
                        nargs='*', help='käsiteltävät kaupungit')
    parser.add_argument('-s', '--start', action='store_true',
                        help='käynnistä server')
    parser.add_argument('-S', '--simulate', action='store_true',
                        help='simulate with data/*.json')
    parser.add_argument('-j', '--use-json', action='store_true',
                        help='tallenna ladatut tiedot json:na')
    parser.add_argument('-t', '--tweet', action='store_true',
                        help='tweettaa muutokset (default print)')
    args = parser.parse_args()

    print(args)

    # Action based on cmd line options
    if args.list_cities:
        if args.cities is None:
            print_cities()
        else:
            print_status(args.cities)
    elif args.start:
        run_server(args.cities, args.tweet, args.use_json, False, args.simulate)
    else:
        parser.print_help()


if __name__ == "__main__":
    print('main.py, launching console_app(), pwd {}', os.getcwd())
    console_app()
