# latubot
Bot for ski track maintenance updates

A personal project for hacking around. Updates can be found in @latubot.

The following env vars are required if -t is used:

LATUBOT_TWITTER_CONSUMER_KEY
LATUBOT_TWITTER_CONSUMER_SECRET
LATUBOT_TWITTER_ACCESS_KEY
LATUBOT_TWITTER_ACCESS_SECRET

To update in Heroku:

* make changes
* git commit
* git push heroku master
* heroku run worker
