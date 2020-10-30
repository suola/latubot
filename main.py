"""Google cloud function entrypoints.

Google cloud functions are easiest to deploy from module named main.py.

Notes:
- call http  : gcloud functions call FUNCTION_NAME --data '{"name":"Keyboard Cat"}'
- call pubsub: gcloud functions call FUNCTION_NAME --data '{"topic":"MY_TOPIC","message":"Hello World!"}'
- check logs:  gcloud functions logs read FUNCTION_NAME
"""

from latubot.gcloud_functions import (
    load_updates_http,
    load_updates_pubsub,
    notify_http,
    notify_pubsub,
)

__all__ = ["load_updates_http", "load_updates_pubsub", "notify_http", "notify_pubsub"]


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    # load_updates(["latu"], ["OULU", "SYOTE"], "6M")
    # notify("12M")
