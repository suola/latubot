"""Google cloud function entry points"""

import logging

import google.cloud.logging

from latubot.notify import notify
from latubot.update import load_updates


def load_updates_http(request):
    """Gcloud function, triggered by http request."""
    sport = filter(None, request.args.get("sport", "latu").split(","))
    area = filter(None, request.args.get("area", "OULU,SYOTE").split(","))
    since = request.args.get("since", None)
    log_level = request.args.get("log_level")

    _init_logging(log_level)

    n = load_updates(sport, area, since)
    return f"Loaded {n} updates"


def load_updates_pubsub(event, context):
    """Gcloud function, triggered by pub/sub event."""
    _init_logging()
    n = load_updates(["latu"], ["OULU", "SYOTE"])
    return f"Loaded {n} updates"


def notify_http(request):
    """Gcloud function, triggered by http request."""
    since = request.args.get("since", None)
    log_level = request.args.get("log_level")

    _init_logging(log_level)

    n = notify(since)
    return f"Sent {n} notifications from updates since {since}"


def notify_pubsub(event, context):
    """Gcloud function, triggered by pub/sub event."""
    _init_logging()
    n = notify()
    return f"Sent {n} notifications"


def _init_logging(level=None):
    """Initialize logging."""
    # https://cloud.google.com/logging/docs/setup/python
    client = google.cloud.logging.Client()

    # Retrieves a Cloud Logging handler based on the environment
    # you're running in and integrates the handler with the
    # Python logging module. By default this captures all logs
    # at INFO level and higher
    client.get_default_handler()
    client.setup_logging(log_level=level or logging.INFO)
