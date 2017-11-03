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
from lxml import html, etree
import json

from latubot.source import cfg
from latubot.source import time_utils

logger = logging.getLogger(__name__)


dumps = partial(json.dumps, cls=time_utils.DateTimeEncoder)
settings = cfg.load()


def load_areas(sport: str=cfg.DEFAULT_SPORT):
    return {area: load_area(area, sport) for area in cfg.area_names(sport)}


def load_area(area: str=cfg.DEFAULT_AREA, sport: str=cfg.DEFAULT_SPORT):
    if area not in cfg.area_names():
        raise ValueError('invalid area %s' % area)

    if sport not in cfg.sport_names():
        raise ValueError('invalid sport %s' % sport)

    updates = _load_updates(area, sport)
    latest = _load_latest(area, sport)
    merged = _merge_updates(updates, latest)

    return merged


def _load_updates(area, sport):
    """Load all updates for (area, sport) from the server."""
    url = cfg.url(settings, area, sport)
    parser = partial(
        _parse_update_html,
        parse_opts=settings['sports'][sport]['html_parser_opts'])
    return _load_updates_from_server(url, parser)


def _load_latest(area, sport):
    """Load latest updates for (area, sport) from the server."""
    url = cfg.url_new(settings, area, sport)
    if url is None:
        return {}

    try:
        return _load_updates_from_server(url, _parse_new_marks_html)
    except requests.exceptions.RequestException:
        logger.debug('failed to load latest for %s, %s', area, sport)
        return {}


def _merge_updates(updates, latest):
    """Merge latest updates into regular updates.

    Sometimes latest updates contain updates not found in regular updates.
    Combine the two.
    """
    if not latest:
        return updates

    merged = updates.copy()
    for city in merged:
        for place in merged[city]:
            if place in latest:
                logger.debug('replace %s-%s \n  "%s" -> "%s"',
                             city, place, merged[city][place], latest[place])
                merged[city][place] = _pick_better(
                        merged[city][place], latest[place])
    return merged


def _pick_better(u1, u2):
    """Pick better of the two updates."""
    if 'date' in u1 and 'date' not in u2:
        return u1
    elif 'date' in u2 and 'date' not in u1:
        return u2
    elif 'date' in u1 and 'date' in u2:
        return u1 if u1['date'] > u2['date'] else u2
    else:
        return u2


def _load_updates_from_server(url: str, parser):
    r = requests.get(url)
    r.raise_for_status()
    data = parser(r.text)
    logger.debug('read and parsed new data from %s' % url)
    return data


def _parse_update_html(text: str, parse_opts: dict):
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


def _parse_status_from_element(pos: html.HtmlElement):
    """Get status from Element."""
    # varies per city
    status_list = pos.xpath('following-sibling::ul')
    status_txt = status_list[0].xpath('descendant-or-self::*')
    strings = filter(None, [x.text.strip() for x in status_txt])
    status = ",".join(s.strip() for s in strings if s)
    return _parse_status_text(status)


def _parse_status_from_element_old(pos: html.HtmlElement):
    """Get status from Element."""
    # old version, worked well with Oulu data
    status_list = pos.xpath('following-sibling::ul/li')
    status_txt = status_list[0].xpath('descendant-or-self::*')
    strings = filter(None, [x.text.strip() for x in status_txt])
    status = ",".join(s.strip() for s in strings if s)
    return status


def _parse_new_marks_html(text: str):
    """Parse loadLatuNewMarks.html page."""
    # Format
    # html.body.div.a name
    # html.body.div.ul.li.text status

    root = etree.HTML(text)
    data = {}
    for div in root.iterfind('.//div'):
        place = div.find('a')
        update = div.find('ul/li')
        if place is not None and update is not None:
            data[place.text.strip()] = _parse_status_text(update.text.strip())

    return data


def _parse_status_text(s: str):
    d = {'txt': s}
    date = time_utils.get_date(s)
    if date:
        d['date'] = date
    return d


def _dump_all(fn: str='areas.json', sport: str=None):
    sport = sport or cfg.DEFAULT_SPORT
    json.dump(load_areas(sport), open(fn, 'w'))


if __name__ == "__main__":
    d1 = load_area(sport='latu')
    print(dumps(d1))
