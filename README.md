# latubot

Bot for ski track maintenance updates

## Introduction

A personal project for hacking around. Updates can be found in Twitter
@latubot.

Currently supports updates from kunto fluentprogress web pages.

## Tweets

Updates into twitter can be enabled by setting environment variables. For
example, for oulu env var must be named `LATUBOT_KEYS_LATU_OULU` to tweet
updates for ski tracks. The value of the env var must contain the following
keys for the twitter account separated by whitespaces:

- consumer key
- consumer secret
- access key
- access secret

All cities with kunto service are listed in
`latubot/source/kunto.py:ALL_AREAS`.

## Deployment

Deployment as AWS lambda is supported with zappa. AWS configuration must be set
properly, deployment can then be done with `zappa deploy dev`. Environment
variables for the supported accounts must be defined either in
`zappa_settings.json` or defined manually in AWS console.
