"""Google cloud function entry points"""

import logging

from latubot.notify import notify
from latubot.update import load_updates


def load_updates_http(request):
    """Gcloud function, triggered by http request."""
    sport = tuple(filter(None, request.args.get("sport", "latu").split(",")))
    area = tuple(filter(None, request.args.get("area", "OULU,SYOTE").split(",")))
    since = request.args.get("since", None)
    log_level = request.args.get("log_level")

    _init_logging(log_level)

    n = load_updates(sport, area, since)
    return f"Loaded {n} updates"


def notify_http(request):
    """Gcloud function, triggered by http request."""
    since = request.args.get("since", None)
    tweet = "tweet" in request.args
    log_level = request.args.get("log_level")

    _init_logging(log_level)

    n = notify(since, tweet)
    return f"Sent {n} notifications from updates since {since}"


def _init_logging(level=None):
    """Initialize logging."""
    if level:
        log_level = getattr(logging, level.upper())
    else:
        log_level = logging.INFO

    logging.basicConfig(level=log_level, format="%(asctime)s: %(message)s")
