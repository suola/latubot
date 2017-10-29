"""API for latubot

- sport (latu, luistelu)
- area (OULU, SYOTE)
- city (oulu, haukipudas)
- place ("Iinatti 8km"...)

v1/
v1/{latu,luistelu}
v1/latu/
v1/latu/oulu
v1/latu/oulu?updated=5m
"""

from datetime import datetime

from flask import Flask, jsonify, abort, request

import raw
import time_utils

app = Flask(__name__)


@app.route('/v1/', methods=['GET'])
def get_sports():
    return jsonify(raw.sport_names())


@app.route('/v1/<string:sport>/', methods=['GET'])
def get_areas(sport):
    sport = sport.lower()
    if sport not in raw.sport_names():
        abort(404, 'invalid sport "%s"' % sport)

    all_ = request.args.get('all', False)
    if all_:
        return jsonify(raw.load_areas(sport))
    else:
        return jsonify(raw.area_names(sport))


@app.route('/v1/<string:sport>/<string:area>/', methods=['GET'])
def get_area(sport, area):
    sport = sport.lower()
    if sport not in raw.sport_names():
        abort(404, 'invalid sport "%s"' % sport)

    area = area.upper()
    if area not in raw.area_names():
        abort(404, 'invalid area "%s"' % area)

    data = raw.load_area(area, sport)

    # ?raw=True to return raw data
    if request.args.get('raw', False):
        return jsonify(data)

    # From now only interested in parsed date, raw is dropped
    dates = pick_dates(data)

    # ?since=<timespan> to include newest elements only
    since = request.args.get('since', None)
    if since:
        dates = filter_data(dates, _time_filter(since))

    # all=True to include empty items as well
    if not request.args.get('all', False):
        dates = remove_empty(dates)

    return jsonify(dates)


def pick_dates(data):
    return {a: {k: v.get('_date') for k, v in d.items()}
            for a, d in data.items()}


def filter_data(data, f):
    nd = {a: {k: v for k, v in d.items() if f(v)} for a, d in data.items()}
    return nd


def remove_empty(data):
    """Remove 1st empty places, then cities."""
    r = {a: {k: v for k, v in d.items() if v} for a, d in data.items()}
    r = {a: d for a, d in r.items() if d}
    return r


def _basic_filter(all_):
    """If all_=True include all items, otherwise only ones with date."""
    def f(v):
        return all_ or '_date' in v
    return f


def _time_filter(since):
    if since.endswith('m'):
        mins = int(since[:-1])
    elif since.endswith('h'):
        mins = 60 * int(since[:-1])
    elif since.endswith('d'):
        mins = 24*60 * int(since[:-1])
    elif since.endswith('M'):
        mins = 31*24*60 * int(since[:-1])
    else:
        mins = int(since)

    def f(v):
        if v is None:
            return False
        else:
            dt = datetime.strptime(v, raw.DATE_FMT)
            return time_utils.is_within(dt, mins)
    return f


if __name__ == '__main__':
    app.run(debug=True)
