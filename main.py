"""Google cloud function entrypoints.

Example update document:

{'id': 3177061, 'name': 'Salonpään yhdyslatu', 'type': 'skitrack', 'group': 'Oulunsalo', 'description': '', status': 'CLOSED', 'images': [], 'date': datetime.datetime(2019, 3, 25, 13, 28, 49, 171000, tzinfo=tzoffset(None, 7200))}

"""

import logging
import hashlib
from typing import Iterable

from google.cloud import firestore

from latubot.source import api

db = None
logger = logging.getLogger(__name__)


def load_updates_http(request=None):
    _load_updates()
    return "Done"


def load_updates_pubsub(event, context):
    pass


def _load_updates():
    """Load updates from kunto into firestore storage."""
    # Lazy init db
    global db
    if db is None:
        logger.info("Initialize firestone client")
        db = firestore.Client()

    location_keys = ("type", "group", "name")
    status_keys = ("date", "status", "description")
    updates = api.load("latu", "OULU")
    for update in updates:
        location = {k: v for k, v in update.items() if k in location_keys}
        status = {k: v for k, v in update.items() if k in status_keys}

        doc_name = location_doc_name(location)
        doc_ref = db.collection("updates").document(doc_name)
        doc_ref.set(location, merge=True)

        if not status.get("date"):
            logger.debug(f"No date for update to {location}, skip")
            continue

        status_doc_name = str(status["date"].timestamp())
        status_ref = doc_ref.collection("statuses").document(status_doc_name)
        status_doc = status_ref.get()
        if status_doc.exists:
            logger.debug(f"Status already exists in {location}")
        else:
            status_ref.set(status)

    logger.info(f"Loaded {len(updates)} updates")


def location_doc_name(location):
    """Get unique document name for a location."""
    return hash_(location.values())[:8]


def hash_(items: Iterable[str]):
    """Calculate hash of items."""
    m = hashlib.sha256()
    for item in items:
        m.update(item.encode())
        m.update(b"\xc0")
    return m.hexdigest()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    load_updates_http()
