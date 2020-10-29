"""Google cloud function entrypoints.

Example update document:

{'id': 3177061, 'name': 'Salonpään yhdyslatu', 'type': 'skitrack', 'group': 'Oulunsalo', 'description': '', status': 'CLOSED', 'images': [], 'date': datetime.datetime(2019, 3, 25, 13, 28, 49, 171000, tzinfo=tzoffset(None, 7200))}


load_updates():
    - read  updates from kunto servers
    - save updates in firestore

notify(since):
    - find updates within since (firestore query)
    - limit newest update per location (in app)
    - find updates not notified within notification-rate-minutes
    - notify
      - save notification time
      - send notification

Notes:
- call http  : gcloud functions call FUNCTION_NAME --data '{"name":"Keyboard Cat"}'
- call pubsub: gcloud functions call FUNCTION_NAME --data '{"topic":"MY_TOPIC","message":"Hello World!"}'
- check logs:  gcloud functions logs read FUNCTION_NAME
"""

import logging
import hashlib
from datetime import datetime, timezone, timedelta
from itertools import product
from collections import defaultdict
from typing import Iterable, Mapping

from google.cloud import firestore

from latubot.source import api
from latubot.time_utils import since_to_delta
from latubot import cfg

db = None
logger = logging.getLogger(__name__)


# Google cloud entry points

def load_updates_http(request):
    """Gcloud function, triggered by http request."""
    sport=filter(None, request.args.get("sport", "").split(","))
    area=filter(None, request.args.get("area", "").split(","))
    since=request.args.get("since", None)
    n = _load_updates(sport, area, since)
    return f"Loaded {n} updates"


def load_updates_pubsub(event, context):
    """Gcloud function, triggered by pub/sub event."""
    n = _load_updates(["latu"], ["OULU", "SYOTE"])
    return f"Loaded {n} updates"


def notify_http(request):
    """Gcloud function, triggered by http request."""
    since=request.args.get("since", None)
    n = _notify(since)
    return f"Sent {n} notifications from updates since {since}"


def notify_pubsub(event, context):
    """Gcloud function, triggered by pub/sub event."""
    n = _notify()
    return f"Sent {n} notifications"


def _load_updates(sports=None, areas=None, since=None):
    """Load updates from kunto into firestore storage."""

    sports = sports or api.sport_names()
    areas = areas or api.area_names()

    i = 0
    for i, update in enumerate(_gen_updates(sports, areas, since)):
        _save_update(update)

    logger.info(f"Loaded {i} updates")
    return i


def get_db():
    """Lazy init db"""
    global db
    if db is None:
        logger.info("Initialize firestone client")
        db = firestore.Client()
    return db


def _gen_updates(sports, areas, since):
    """Load updates from all sports and areas."""
    for sport, area in product(sports, areas):
        logger.info(f"Load {sport}, {area}")
        for update in api.load(sport, area, since):
            update["area"] = area
            yield update


_location_keys = ("area", "type", "group", "name")
_status_keys = ("date", "status", "description")


def _save_update(update):
    """Save update in firestore db."""
    location = {k: v for k, v in update.items() if k in _location_keys}
    status = {k: v for k, v in update.items() if k in _status_keys}
    status["location"] = _location_doc_name(location)

    doc_ref = _save_location(location)
    updated = _save_status(doc_ref, status)
    logger.debug(f"{location} updated {updated}")

    
def _save_location(location):
    """Save location in db, return reference to the document."""
    doc_name = _location_doc_name(location)
    doc_ref = get_db().collection("locations").document(doc_name)
    doc = doc_ref.get()
    if True or not doc.exists:
        doc_ref.set(location)
    return doc_ref


def _save_status(doc_ref, status):
    """Save status in db."""
    if not status.get("date"):
        logger.debug(f"No date in {status}, skip")
        return

    status_doc_name = _status_doc_name(status)
    status_ref = doc_ref.collection("updates").document(status_doc_name)
    status_ref.set(status)
    return True

    status_doc = status_ref.get()
    if status_doc.exists:
        return False
    else:
        status_ref.set(status)


def _location_doc_name(location):
    """Get unique document name for a location."""
    values = (location.get(k) for k in _location_keys)
    return _hash(values)[:8]


def _status_doc_name(status):
    """Get unique document name for a status update."""
    return str(status["date"].timestamp())


def _hash(items: Iterable[str]):
    """Calculate hash of items."""
    m = hashlib.sha256()
    for item in items:
        m.update(item.encode())
        m.update(b"\xc0")
    return m.hexdigest()


### For notifications

def _find_updates(since: str):
    """Find all updates since."""
    delta = since_to_delta(since)
    dt = datetime.now(timezone.utc) - delta
    query = get_db().collection_group("updates").where("date", ">", dt)
    return list(doc.to_dict() for doc in query.stream())


def _find_newest_update_by_location(updates: Iterable) -> Iterable:
    """Find newest update for each location."""
    d = defaultdict(list)
    for update in updates:
        d[update["location"]].append(update)

    for k, v in d.items():
        d[k] = max(v, key=lambda x: x["date"])

    return d.values()


def _gen_updates_to_notify(updates):
    """Find which updates should be notified."""
    for update in updates:
        last_notified = _find_last_notified(update["location"])
        delta_last_update = update["date"] - (last_notified or datetime.min.replace(tzinfo=timezone.utc))
        delta_now = datetime.now(timezone.utc) - update["date"]
        if delta_last_update < timedelta(minutes=cfg.MIN_MINS_BETWEEN_UPDATES):
            logger.debug(f"Skip {update['location']} last notified {delta_last_update} ago")
        elif delta_last_update < timedelta(minutes=cfg.MIN_MINS_BETWEEN_UPDATES):
            logger.debug(f"Skip {update['location']} update too old {delta_now}")
        else:
            logger.debug(f"Notify {update['location']}, previously {delta_last_update} ago")
            yield update


def _find_last_notified(location):
    """Find when an update for location was previously notified.

    Returns notification time as datetime object or None if never notified.
    """
    doc_ref = get_db().collection("locations").document(location)
    doc = doc_ref.get()
    if not doc.exists:
        return None
    else:
        return doc.to_dict().get("last_notified")


def _notify(since="15m"):
    since = since or "15m"
    updates = _find_updates(since)
    logger.info(f"Found {len(updates)} updates within last {since}")
    if not updates:
        return

    newest_updates = _find_newest_update_by_location(updates)
    logger.info(f"Found updates for {len(newest_updates)} different locations")
    i = 0
    for i, update in enumerate(_gen_updates_to_notify(newest_updates)):
        _notify_one_update(update)

    return i


def _notify_one_update(update):
    """Notify one update."""
    _send_notification(update)
    _save_notification_time(update)


def _send_notification(update):
    """Send notification for an update."""
    print(f"Update {update}")


def _save_notification_time(update):
    """Save notification time of an update into firestore db."""
    doc_ref = get_db().collection("locations").document(update["location"])
    doc_ref.set({"last_notified": update["date"]}, merge=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # _load_updates(["latu"], ["OULU", "SYOTE"])
    _notify("6M")
