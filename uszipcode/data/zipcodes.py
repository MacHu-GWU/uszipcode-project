# -*- coding: utf-8 -*-

"""
What every step of the pipeline needs to know about a ZIP code.
"""

import typing


def normalize_zip(value) -> typing.Optional[str]:
    """
    Return the 5-digit ZIP as a string with leading zeros, or None if ``value``
    is not a ZIP code. ``"501"`` -> ``"00501"``; ``"00000"``, ``"99999"``
    (used as totals / "other" in some files) and non-digits -> None.
    """
    if value is None:
        return None
    s = str(value).strip()
    if s.endswith(".0"):  # numbers read from spreadsheets
        s = s[:-2]
    if not s.isdigit() or len(s) > 5:
        return None
    s = s.zfill(5)
    if s in ("00000", "99999"):
        return None
    return s
