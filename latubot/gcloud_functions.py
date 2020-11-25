"""Google cloud function entry points"""

import logging
import json

from latubot.notify import notify, get_updates
from latubot.update import load_updates
from latubot.time_utils import DateTimeEncoder


def load_updates_http(request):
    """Gcloud function, triggered by http request."""
    sport = tuple(filter(None, request.args.get("sport", "latu").split(",")))
    area = tuple(filter(None, request.args.get("area", "OULU,SYOTE").split(",")))
    since = request.args.get("since", None)
    log_level = request.args.get("log_level")

    _init_logging(log_level)

    n = load_updates(sport, area, since)
    return f"Loaded {n} new updates"


def notify_http(request):
    """Gcloud function, triggered by http request."""
    since = request.args.get("since", None)
    tweet = "tweet" in request.args
    log_level = request.args.get("log_level")

    _init_logging(log_level)

    n = notify(since, tweet)
    return f"Sent {n} notifications from updates since {since}"


def get_updates_http(request):
    """Gcloud function, triggered by http request."""
    filter_ = request.args.get("filter")
    n = int(request.args.get("n", 10))
    log_level = request.args.get("log_level")

    _init_logging(log_level)

    updates = get_updates(filter_, n)
    return json.dumps(updates, indent=2, cls=DateTimeEncoder, sort_keys=True)


def _init_logging(level=None):
    """Initialize logging."""
    if level:
        log_level = getattr(logging, level.upper())
    else:
        log_level = logging.INFO

    logging.basicConfig(level=log_level, format="%(asctime)s: %(message)s")
