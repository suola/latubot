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
import datetime
import logging

import requests
from lxml import html
import json

# Configuration
BASE = "https://kunto.softroi.fi/LATU{area}/"
STATUS_LATU = BASE + "latuui/loadLatuStatusListAccordion.html"
STATUS_LUISTELU = BASE + "latuui/loadLuisteluStatusListAccordion.html"
LATEST = BASE + "latuui/loadLatuNewMarks.html"
MESSAGES = BASE + "latuui/loadLatuInfoMessageList.html"
IDS = BASE + "data/oulu/latu2shpid.json"
GML = BASE + "data/oulu/ladut.gml"
# Script urls for other resources were found
ACCORDION_SCRIPT = BASE + "script/frLatuMapAccordion.jsp"

# areas w/ service (how to get this list dynamically?)
_AREAS = ('OULU', 'SYOTE', 'SOTKAMOVUOKATTI', 'KOLI', 'YLIVIESKA', 'TORNIO',
          'PIEKSAMAKI', 'KUOPIO', 'KAJAANI', 'HAMEENLINNA', 'KIRKKONUMMI',
          'VARKAUS', 'HYVINKAA', 'NIVALA', 'RAASEPORI',)

_DEFAULT_AREA = 'OULU'

# available sports
_SPORTS = {
        'latu': {
            'url': STATUS_LATU,
            'areas': _AREAS,
            'acc_label': 'accordion'
            },
        'luistelu': {
            'url': STATUS_LUISTELU,
            'areas': _AREAS,
            'acc_label': 'accordion2'
            },
        }


_DEFAULT_SPORT = 'latu'

# Date format used internally
DATE_FMT = '%Y-%m-%d %H:%M'

logger = logging.getLogger(__name__)


def sport_names():
    return list(_SPORTS.keys())


def area_names(sport=None):
    sport = sport or _DEFAULT_SPORT
    return _SPORTS[sport]['areas']


def load_areas(sport=None):
    sport = sport or _DEFAULT_SPORT
    return {area: load_area(area, sport) for area in area_names(sport)}


def load_area(area=None, sport=None):
    area = area or _DEFAULT_AREA
    if area not in area_names():
        raise ValueError('invalid area %s' % area)

    sport = sport or _DEFAULT_SPORT
    if sport not in sport_names():
        raise ValueError('invalid sport %s' % sport)

    base_url = _SPORTS[sport]['url']
    url = base_url.format(area=area)
    parser = partial(_parse_update_html, acc_label=_SPORTS[sport]['acc_label'])
    return _load_updates_from_server(url, parser)


def _load_updates_from_server(url, parser):
    r = requests.get(url)
    r.raise_for_status()
    data = parser(r.text)
    logger.debug('read and parsed new data from %s' % url)
    return data


def _parse_update_html(text, acc_label):
    # Format
    # html.body.div.h3.a kaupunki
    # html.body.div.div<id="l_g9">.span[2].text name
    # html.body.div.div<id="l_g9">.ul.li.text status

    # latu updates use 'accordion', luistelu 'accordion2'
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
    d = {'raw': s}
    date = _get_date(s)
    if date:
        d['_date'] = date.strftime(DATE_FMT)
    return d


def _get_date(s):
    """Get date from s, None if fails."""
    _fmt = 'Kunnostettu: %d.%m. klo %H:%M'
    try:
        date = datetime.datetime.strptime(s, _fmt)
    except ValueError:
        return None

    now = datetime.datetime.now()
    new_date = date.replace(year=now.year)
    if new_date > now:
        new_date = date.replace(year=now.year-1)
    return new_date


def _dump_all(fn='areas.json', sport=None):
    sport = sport or _DEFAULT_SPORT
    json.dump(load_areas(sport), open(fn, 'w'))


if __name__ == "__main__":
    print(load_area(sport='luistelu'))
    # _dump_all('all_luistelu.json', sport='luistelu')
