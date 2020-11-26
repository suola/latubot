"""Notification functions.

- find updates to notify
  - find all update docs from db since
  - skip if notified too recently
  - skip if update already too old
- notify
  - save notification time
  - send notification
"""

import logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from itertools import islice
from typing import Iterable

from google.cloud import firestore

from latubot.time_utils import since_to_delta
from latubot.gcloud import get_db
from latubot import cfg
from latubot.tweet import tweet_update
from latubot.update import load_location

logger = logging.getLogger(__name__)


def get_updates(filter_=None, n=10):
    """Get latest updates."""
    filter_keys = ("name", "group", "area")

    def f(update):
        return filter_ is None or any(filter_ in update[k] for k in filter_keys)

    filtered_updates = filter(f, _find_latest_updates())
    return tuple(islice(filtered_updates, n))


def _find_latest_updates():
    """Generate update documents from firestore in reverse order."""
    query = (
        get_db()
        .collection_group("updates")
        .order_by("date", direction=firestore.Query.DESCENDING)
    )
    for doc_ref in query.stream():
        doc = doc_ref.to_dict()
        location = load_location(doc["location"])
        yield {**location, **doc}


def notify(since="15m", tweet=False):
    """Send notifications for updates."""
    since = since or "15m"

    i = 0
    for i, update in enumerate(_find_updates(since)):
        _notify_one_update(update, tweet)

    return i


def _find_updates(since: str):
    """Find updates from firestore db since."""
    updates = _find_update_docs_since(since)
    newest_update_per_location = _find_newest_update_by_location(updates)
    logger.info(f"Found {len(newest_update_per_location)} updates since {since}")
    yield from _gen_updates_to_notify(newest_update_per_location)


def _find_update_docs_since(since: str):
    """Find all update documents from firestore since."""
    delta = since_to_delta(since)
    earliest_dt = datetime.now(timezone.utc) - delta
    query = get_db().collection_group("updates").where("date", ">", earliest_dt)
    return (doc.to_dict() for doc in query.stream())


def _find_newest_update_by_location(updates: Iterable) -> Iterable:
    """Limit to newest update for each location."""
    d = defaultdict(list)
    for update in updates:
        d[update["location"]].append(update)

    for k, v in d.items():
        d[k] = max(v, key=lambda x: x["date"])

    return d.values()


def _gen_updates_to_notify(updates):
    """Generate updates that should be notified."""
    for update in updates:
        update_age = datetime.now(timezone.utc) - update["date"]
        if update_age > timedelta(minutes=cfg.MAX_UPDATE_AGE_TO_NOTIFY) > timedelta(0):
            logger.debug(f"Skip {update['location']} update too old {update_age}")
            continue

        previously_notified = _find_last_notified(update["location"])
        if previously_notified is None:
            logger.debug(f"Notify {update['location']}, never notified before")
            yield update
            continue

        delta_since_previous_update = update["date"] - previously_notified
        if delta_since_previous_update < timedelta(
            minutes=cfg.MIN_MINS_BETWEEN_UPDATES
        ):
            logger.debug(
                f"Skip {update['location']} last notified {delta_since_previous_update} ago"
            )
        else:
            logger.debug(
                f"Notify {update['location']}, previously {delta_since_previous_update} ago"
            )
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


def _notify_one_update(update, tweet):
    """Notify one update."""
    _send_notification(update, tweet)
    _save_notification_time(update)


def _send_notification(update, tweet):
    """Send notification for an update."""
    tweet_update(update, not tweet)


def _save_notification_time(update):
    """Save notification time of an update into firestore db."""
    doc_ref = get_db().collection("locations").document(update["location"])
    doc_ref.set({"last_notified": update["date"]}, merge=True)
