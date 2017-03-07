"""Settings for latubot
"""

import os
import os.path as op
import configparser

# Global config, initialized only once in _init_cfg(), read from everywhere
cfg = None


def _init_cfg():
    """Initialize config from local settings file or env vars"""
    global cfg

    if cfg is not None:
        return

    # If local settings file exists, read config from [latubot] section in
    # the config file, otherwise use env vars
    if op.exists('latubot.ini'):
        _cfg = configparser.ConfigParser()
        _cfg.read('latubot.ini')
        cfg = {k.upper():v for k,v in _cfg._sections['latubot'].items()}
        print('read config (%d vars) from local config file' % len(cfg))
    else:
        # Read all env vars prefixed w/ LATUBOT_, but exclude LATUBOT_ from the
        # values
        cfg = {k[8:]:v for k,v in os.environ.items() if
               k.startswith('LATUBOT_')}
        print('read config (%d vars) from env' % len(cfg))


# Initialize config on import
_init_cfg()
