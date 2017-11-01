"""Fetch and parse data from foreign server.

Structure for AREA

{
'CITY1': {
  'LATU1': 'status',
  'LATU2': 'status',
  ...
},
...
}
"""

from functools import partial
import logging

import requests
from lxml import html
import json

from latubot import cfg
from . import time_utils

logger = logging.getLogger(__name__)


settings = cfg.load()


def sport_names():
    return list(settings['sports'].keys())


def area_names(sport=cfg.DEFAULT_SPORT):
    return settings['sports'][sport]['areas']


def load_areas(sport=cfg.DEFAULT_SPORT):
    return {area: load_area(area, sport) for area in area_names(sport)}


def load_area(area=cfg.DEFAULT_AREA, sport=cfg.DEFAULT_SPORT):
    if area not in area_names():
        raise ValueError('invalid area %s' % area)

    if sport not in sport_names():
        raise ValueError('invalid sport %s' % sport)

    url = cfg.url(settings, area, sport)
    parser = partial(_parse_update_html,
                     parse_opts=settings['sports'][sport]['html_parser_opts'])
    return _load_updates_from_server(url, parser)


def _load_updates_from_server(url, parser):
    r = requests.get(url)
    r.raise_for_status()
    data = parser(r.text)
    logger.debug('read and parsed new data from %s' % url)
    return data


def _parse_update_html(text, parse_opts):
    # Format
    # html.body.div.h3.a kaupunki
    # html.body.div.div<id="l_g9">.span[2].text name
    # html.body.div.div<id="l_g9">.ul.li.text status

    acc_label = parse_opts['acc_label']
    assert acc_label in ('accordion', 'accordion2')
    tree = html.fromstring(text)
    data = {}
    for city_list in tree.xpath('//*[@id="%s"]/div' % acc_label):
        try:
            city = city_list.xpath(
                    'preceding-sibling::h3[1]/a')[0].text.strip()
        except IndexError:
            continue
        data[city] = {}
        positions = city_list.xpath('div/span[2]')
        for pos in positions:
            data[city][pos.text.strip()] = _parse_status_from_element(pos)

    return data


def _parse_status_from_element(pos):
    """Get status from Element."""
    # varies per city
    status_list = pos.xpath('following-sibling::ul')
    status_txt = status_list[0].xpath('descendant-or-self::*')
    strings = filter(None, [x.text.strip() for x in status_txt])
    status = ",".join(s.strip() for s in strings if s)
    return _parse_status_text(status)


def _parse_status_from_element_old(pos):
    """Get status from Element."""
    # old version, worked well with Oulu data
    status_list = pos.xpath('following-sibling::ul/li')
    status_txt = status_list[0].xpath('descendant-or-self::*')
    strings = filter(None, [x.text.strip() for x in status_txt])
    status = ",".join(s.strip() for s in strings if s)
    return status


def _parse_status_text(s):
    d = {'txt': s}
    date = time_utils.get_date(s)
    if date:
        d['date'] = date
    return d


def _dump_all(fn='areas.json', sport=None):
    sport = sport or cfg._EFAULT_SPORT
    json.dump(load_areas(sport), open(fn, 'w'))


if __name__ == "__main__":
    print(load_area(sport='luistelu'))
    # _dump_all('all_luistelu.json', sport='luistelu')
