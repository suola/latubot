from datetime import datetime, timedelta


def is_within(td: datetime, mins: int):
    """is td within mins minutes from now?"""
    assert mins >= 0
    td_ref = datetime.now() - timedelta(minutes=mins)
    return td > td_ref


def get_date(s):
    """Get date from s, None if fails."""
    _fmt = 'Kunnostettu: %d.%m. klo %H:%M'
    try:
        date = datetime.strptime(s, _fmt)
    except ValueError:
        return None

    now = datetime.now()
    new_date = date.replace(year=now.year)
    if new_date > now:
        new_date = date.replace(year=now.year-1)
    return new_date


def since_to_mins(since):
    if since.endswith('m'):
        mins = int(since[:-1])
    elif since.endswith('h'):
        mins = 60 * int(since[:-1])
    elif since.endswith('d'):
        mins = 24*60 * int(since[:-1])
    elif since.endswith('M'):
        mins = 31*24*60 * int(since[:-1])
    else:
        mins = int(since)

    return mins
