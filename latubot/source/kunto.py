"""Fetch and parse data from KUNTO servers.

BASE = "https://kunto.softroi.fi/LATU{area}/"
STATUS_LATU = BASE + "latuui/loadLatuStatusListAccordion.html"
STATUS_LUISTELU = BASE + "latuui/loadLuisteluStatusListAccordion.html"
LATEST = BASE + "latuui/loadLatuNewMarks.html"
MESSAGES = BASE + "latuui/loadLatuInfoMessageList.html"
IDS = BASE + "data/oulu/latu2shpid.json"
GML = BASE + "data/oulu/ladut.gml"
# Script urls for other resources were found
ACCORDION_SCRIPT = BASE + "script/frLatuMapAccordion.jsp"
"""

import logging
import re
from datetime import datetime
import json

import requests
from lxml import html, etree

logger = logging.getLogger(__name__)


# all areas that use SOFTROI kunto service
ALL_AREAS = (
    'HAMEENLINNA',
    'HYRYNSALMIPUOLANKA',
    'HYVINKAA',
    'IISALMI',
    'KAJAANI',
    'KEMI',
    'KIRKKONUMMI',
    'KOLI',
    'KOUVOLA',
    'KUHMO',
    'KUOPIO',
    'KUUSAMO',
    'MANTSALA',
    'MIKKELI',
    'NIVALA',
    'OULU',
    'PIEKSAMAKI',
    'RAASEPORI',
    'SUOMUSSALMI',
    'SOTKAMOVUOKATTI',
    'SYOTE',
    'TORNIO',
    'VARKAUS',
    'YLIVIESKA')

ALL_SPORTS = ('latu', 'luistelu')

_DEFAULT_AREA = 'OULU'
_DEFAULT_SPORT = 'latu'

"""Configuration for parsing source data."""
_settings = {
    'baseurl': "https://kunto.softroi.fi/LATU{area}/",
    'sports': {
        'latu': {
            "url_accordion": "latuui/loadLatuStatusListAccordion.html",
            "url_new": "latuui/loadLatuNewMarks.html",
            'html_parser_opts': {
                'acc_label': 'accordion',
                },
            },
        'luistelu': {
            "url_accordion": "latuui/loadLuisteluStatusListAccordion.html",
            "url_new": None,
            'html_parser_opts': {
                'acc_label': 'accordion2',
                }
            },
        },
    }


def load(sport: str=_DEFAULT_SPORT, area: str=_DEFAULT_AREA):
    """Load data for (sport, area) combo."""
    if area not in ALL_AREAS:
        raise ValueError('invalid area %s' % area)

    if sport not in _settings['sports'].keys():
        raise ValueError('invalid sport %s' % sport)

    # Load data from all sources and merge
    updates = Accordion(sport, area).load()
    latest = Latest(sport, area).load()
    merged = _merge_updates(updates, latest)

    return merged


def _merge_updates(updates, latest):
    """Merge latest updates into regular updates.

    Sometimes latest updates contain updates not found in regular updates.
    Combine the two. Note that latest doesn't have city info at all,
    need to rely that there are no identical place names in cities.
    """
    if not latest:
        return updates

    merged = updates.copy()
    merged_places = set()
    for city in merged:
        for place in merged[city]:
            if place in latest:
                merged_places.add(place)
                merged[city][place] = _pick_better(
                        merged[city][place], latest[place])
    if merged_places:
        logger.debug('merged latest for %d places', len(merged_places))

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


class Kunto:
    """Base class for parsing subpages from kunto service."""
    tbaseurl = "https://kunto.softroi.fi/LATU{area}/"
    sports = ('latu', 'luistelu')

    def __init__(self, sport, area):
        self.baseurl = self.tbaseurl.format(area=area)
        if sport not in self.sports:
            raise ValueError(f'Invalid sport {sport}')
        self.sport = sport
        self.area = area

    @classmethod
    def _parse_status_text(cls, s: str):
        """Parse status text."""
        d = {'txt': s}
        date = cls.get_date(s)
        if date:
            d['date'] = date
        return d

    @staticmethod
    def get_date(s):
        """Get date from s, None if fails."""
        # In regular updates there is a colon, in latest updates -list there
        # isn't
        m = re.match('Kunnostettu(:)? (.*)', s)
        if m and len(m.groups()) == 2:
            date_str = m.group(2)
        else:
            return None

        # str -> datetime
        _fmt = '%d.%m. klo %H:%M'
        try:
            date = datetime.strptime(date_str, _fmt)
        except ValueError:
            return None

        # guess the missing year
        now = datetime.now()
        new_date = date.replace(year=now.year)
        if new_date > now:
            new_date = date.replace(year=now.year-1)
        return new_date


class Accordion(Kunto):
    """Load updates from Accordion page."""
    _cfgs = {
        'latu': {
            'url': 'latuui/loadLatuStatusListAccordion.html',
            'html_parser_opts': {
                'acc_label': 'accordion',
                }
            },
        'luistelu': {
            'url': 'latuui/loadLuisteluStatusListAccordion.html',
            'html_parser_opts': {
                'acc_label': 'accordion2',
                }
            },
        }

    def __init__(self, sport, area):
        super().__init__(sport, area)
        self.cfg = self._cfgs[sport]
        self.url = self.baseurl + self.cfg['url']

    def load(self):
        r = requests.get(self.url)
        r.raise_for_status()
        data = self._parse_html(r.text,
            parse_opts=self.cfg['html_parser_opts'])
        logger.debug('read and parsed data from %s' % self.url)
        return data

    @classmethod
    def _parse_html(cls, text: str, parse_opts: dict):
        # Format
        # html.body.div.h3.a kaupunki
        # html.body.div.div<id="l_g9">.span[2].text name
        # html.body.div.div<id="l_g9">.ul.li.text status

        acc_label = parse_opts['acc_label']
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
                data[city][pos.text.strip()] = \
                        cls._parse_status_from_element(pos)

        return data

    @classmethod
    def _parse_status_from_element(cls, pos: html.HtmlElement):
        """Get status from Element."""
        # varies per city
        status_list = pos.xpath('following-sibling::ul')
        status_txt = status_list[0].xpath('descendant-or-self::*')
        strings = filter(None, [x.text.strip() for x in status_txt])
        status = ",".join(s.strip() for s in strings if s)
        return cls._parse_status_text(status)


class Latest(Kunto):
    """Load updates from latest page."""

    _cfgs = {
        'latu': {
            'url': 'latuui/loadLatuNewMarks.html',
            },
        'luistelu': None
        }

    def __init__(self, sport, area):
        super().__init__(sport, area)
        self.cfg = self._cfgs[sport]
        if self.cfg is None:
            return
        self.url = self.baseurl + self.cfg['url']

    def load(self):
        if self.cfg is None:
            return {}

        try:
            r = requests.get(self.url)
            r.raise_for_status()
        except requests.exceptions.RequestException:
            logger.debug('failed to load latest for %s, %s',
                    self.sport, self.area)
            return {}

        data = self._parse_html(r.text)
        logger.debug('read and parsed data from %s' % self.url)
        return data

    @classmethod
    def _parse_html(cls, text: str):
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
                data[place.text.strip()] = \
                    cls._parse_status_text(update.text.strip())

        return data



# for testing and debugging
def _load_areas(sport: str=_DEFAULT_SPORT):
    return {area: load_area(sport, area) for area in ALL_AREAS}


def _dump_all(fn: str='areas.json', sport: str=None):
    sport = sport or _DEFAULT_SPORT
    json.dump(_load_areas(sport), open(fn, 'w'))


if __name__ == "__main__":
    from latubot.source import time_utils

    logging.basicConfig(level=logging.DEBUG)
    d1 = load(sport='latu')
    print(json.dumps(d1, cls=time_utils.DateTimeEncoder))
