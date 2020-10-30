"""Update functions.

- read updates from kunto servers
- save updates in firestore db

Example update document:

{
  'id': 3177061,
  'name': 'Salonpään yhdyslatu',
  'type': 'skitrack',
  'group': 'Oulunsalo',
  'description': '',
  'status': 'CLOSED',
  'images': [],
  'date': datetime.datetime(2019, 3, 25, 13, 28, 49, 171000, tzinfo=tzoffset(None, 7200))
}


"""

import logging
import hashlib
from itertools import product
from typing import Iterable

from latubot.source import api
from latubot.gcloud import get_db

logger = logging.getLogger(__name__)


def load_updates(sports=None, areas=None, since=None):
    """Load updates from kunto into firestore storage."""

    sports = sports or api.sport_names()
    areas = areas or api.area_names()
    logger.info(f"Load updates for {sports} in {areas} since {since}")

    i = 0
    for i, update in enumerate(_gen_updates(sports, areas, since)):
        _save_update(update)

    logger.info(f"Loaded {i} updates")
    return i


def _gen_updates(sports, areas, since):
    """Load updates from all sports and areas."""
    for sport, area in product(sports, areas):
        logger.debug(f"Load {sport}, {area}")
        for update in api.load(sport, area, since):
            update["area"] = area
            yield update


_location_keys = ("area", "type", "group", "name")
_update_keys = ("date", "status", "description")


def _save_update(update):
    """Save one update in firestore db."""
    location = {k: v for k, v in update.items() if k in _location_keys}
    status = {k: v for k, v in update.items() if k in _update_keys}
    # Save location in status to enable back referencing location from a status
    status["location"] = _location_doc_name(location)

    location_doc_ref = _save_location(location)
    updated = _save_status(location_doc_ref, status)
    if updated:
        logger.debug(f"{location} updated")


def _save_location(location):
    """Save a location in db, return reference to the document."""
    doc_name = _location_doc_name(location)
    doc_ref = get_db().collection("locations").document(doc_name)
    doc = doc_ref.get()
    if not doc.exists:
        doc_ref.set(location)
    return doc_ref


def _save_status(doc_ref, status):
    """Save a status update in db."""
    if not status.get("date"):
        logger.debug(f"No date in {status}, skip")
        return

    status_doc_name = _status_doc_name(status)
    status_ref = doc_ref.collection("updates").document(status_doc_name)
    status_doc = status_ref.get()

    if status_doc.exists:
        return False
    else:
        status_ref.set(status)
        return True


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
