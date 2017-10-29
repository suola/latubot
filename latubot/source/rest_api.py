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

from . import api
from . import raw

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
    raw_response = request.args.get('raw', False)
    since = request.args.get('since', None)
    empty = request.args.get('all', False)

    try:
        data = api.get_area(sport, area, raw_response, since, empty)
    except ValueError as e:
        abort(404, e)

    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)
