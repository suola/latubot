"""Google cloud function entrypoints.

Google cloud functions are easiest to deploy from module named main.py.

TODO:
- verify logging
- deploy scheduler jobs from here

Notes:
- call http  : gcloud functions call FUNCTION_NAME --data '{"name":"Keyboard Cat"}'
- call pubsub: gcloud functions call FUNCTION_NAME --data '{"topic":"MY_TOPIC","message":"Hello World!"}'
- check logs:  gcloud functions logs read FUNCTION_NAME
- scheduler:   gcloud scheduler jobs list
-              gcloud scheduler jobs describe <job-name>
"""

from latubot.gcloud_functions import (
    load_updates_http,
    notify_http,
)

__all__ = ["load_updates_http", "notify_http"]
