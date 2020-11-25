"""Run latubot functions from the cli"""

import argparse
import logging
import json

from latubot.notify import notify, get_updates
from latubot.update import load_updates
from latubot.time_utils import DateTimeEncoder

logger = logging.getLogger(__name__)


def main(parser):
    args = parser.parse_args()
    log_level = max(1, logging.WARNING - 10 * args.verbose)
    _LOG_FORMAT = "%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s"
    logging.basicConfig(level=log_level, format=_LOG_FORMAT)
    logging.Formatter.default_msec_format = "%s.%03d"

    if "func" in args:
        args.func(args)
    else:
        parser.print_help()


def _update(args):
    logger.info(f"_update {args}")
    load_updates(_split(args.sports), _split(args.areas), args.since)


def _notify(args):
    logger.info(f"_notify {args}")
    notify(args.since)


def _get_updates(args):
    logger.info(f"_get_updates {args}")
    print(json.dumps(get_updates(args.filter, args.n), indent=2, cls=DateTimeEncoder, sort_keys=True))


def arg_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser("latubot cli app")

    # top-level options
    parser.add_argument(
        "--verbose",
        "-V",
        action="count",
        default=0,
        help="logging level, default WARNING, each V lowers level"
        " by 10 (WARNING -> INFO -> DEBUG)",
    )

    # Sub parsers
    subparsers = parser.add_subparsers()

    # update
    update_parser = subparsers.add_parser("update")
    update_parser.set_defaults(func=_update)
    update_parser.add_argument("--sports", "-s", default="latu")
    update_parser.add_argument("--areas", "-a", default="OULU, SYOTE")
    update_parser.add_argument("--since", default="1d")

    # notify
    notify_parser = subparsers.add_parser("notify")
    notify_parser.set_defaults(func=_notify)
    notify_parser.add_argument("--since", default="1h")

    # get_updates
    get_updates_parser = subparsers.add_parser("get_updates")
    get_updates_parser.set_defaults(func=_get_updates)
    get_updates_parser.add_argument("--filter")
    get_updates_parser.add_argument("-n", type=int, default=10)

    return parser


def _split(s):
    return [x.strip() for x in s.split(",")]


if __name__ == "__main__":
    main(arg_parser())
