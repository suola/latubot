"""Settings for raw data sources.

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

# all areas that use SOFTROI kunto service
_ALL_AREAS = (
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


# _SUPPORTED_AREAS = _ALL_AREAS
_SUPPORTED_AREAS = ('OULU', 'SYOTE')

_ALL_SPORTS = ('latu', 'luistelu')

DEFAULT_AREA = 'OULU'
DEFAULT_SPORT = 'latu'


def load():
    """Load app settings."""
    assert set(_SUPPORTED_AREAS) <= set(_ALL_AREAS)
    cfg = {
        'baseurl': "https://kunto.softroi.fi/LATU{area}/",
        'sports': {
            'latu': {
                "areas": _SUPPORTED_AREAS,
                "url": "latuui/loadLatuStatusListAccordion.html",
                "url_new": "latuui/loadLatuNewMarks.html",
                'html_parser_opts': {
                    'acc_label': 'accordion',
                    },
                },
            'luistelu': {
                "areas": _SUPPORTED_AREAS,
                "url": "latuui/loadLuisteluStatusListAccordion.html",
                "url_new": None,
                'html_parser_opts': {
                    'acc_label': 'accordion2',
                    }
                },
            },
        }

    return cfg


def url(c: dict, area: str, sport: str):
    return c['baseurl'].format(area=area) + c['sports'][sport]['url']


def url_new(c: dict, area: str, sport: str):
    if c['sports'][sport]['url_new']:
        return c['baseurl'].format(area=area) + c['sports'][sport]['url_new']
    else:
        return None


def sport_names():
    return _ALL_SPORTS


def area_names(sport: str=DEFAULT_SPORT):
    # TODO: fix to follow defined config
    return _ALL_AREAS
