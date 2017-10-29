from datetime import datetime, timedelta


def is_within(td, mins):
    """is td within mins minutes from now?"""
    assert mins >= 0
    td_ref = datetime.now() - timedelta(minutes=mins)
    return td > td_ref
