"""Google cloud related functionality."""

import logging

from google.cloud import firestore

db = None
logger = logging.getLogger(__name__)


def get_db():
    """Lazy init db"""
    global db
    if db is None:
        logger.info("Initialize firestone client")
        db = firestore.Client()
    return db
