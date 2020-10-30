"""Google cloud function entry points"""

from latubot.notify import notify
from latubot.update import load_updates


def load_updates_http(request):
    """Gcloud function, triggered by http request."""
    sport = filter(None, request.args.get("sport", "latu").split(","))
    area = filter(None, request.args.get("area", "OULU,SYOTE").split(","))
    since = request.args.get("since", None)
    n = load_updates(sport, area, since)
    return f"Loaded {n} updates"


def load_updates_pubsub(event, context):
    """Gcloud function, triggered by pub/sub event."""
    n = load_updates(["latu"], ["OULU", "SYOTE"])
    return f"Loaded {n} updates"


def notify_http(request):
    """Gcloud function, triggered by http request."""
    since = request.args.get("since", None)
    n = notify(since)
    return f"Sent {n} notifications from updates since {since}"


def notify_pubsub(event, context):
    """Gcloud function, triggered by pub/sub event."""
    n = notify()
    return f"Sent {n} notifications"
