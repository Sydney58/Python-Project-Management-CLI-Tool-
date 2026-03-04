"""
utils/validators.py - Input validation helpers

Two things to validate:
  1. Email addresses - uses a regex pattern
  2. Dates - uses python-dateutil for flexible parsing

The email regex isn't perfect (technically valid emails can be really weird)
but it catches the obvious mistakes like "notanemail" or "missing@domain".

The dateutil library is really cool - it can parse stuff like "Dec 31 2025"
or "31/12/2025" or "2025-12-31" all automatically. No need to handle every
format yourself.
"""
from __future__ import annotations

import re

# try to import dateutil - it should always be there since it's in requirements.txt
# but just in case, we fall back to a strict YYYY-MM-DD only mode
try:
    from dateutil import parser as dateutil_parser  # type: ignore
    _DATEUTIL_AVAILABLE = True
except ImportError:
    _DATEUTIL_AVAILABLE = False


# email regex - matches the basic pattern: something@something.something
# not 100% RFC-5322 compliant but good enough for a CLI tool
# I found a much more complex regex online but it was like 200 chars long and scary
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> str:
    """
    Check if an email address looks valid.
    Returns the email unchanged if it passes.
    Raises ValueError if it's invalid.
    Empty string is allowed (email is optional).
    """
    if not email:
        return email  # email is optional, empty is fine
    if not _EMAIL_RE.match(email):
        raise ValueError(f"'{email}' is not a valid email address.")
    return email


def validate_date(date_str: str) -> str:
    """
    Parse and validate a date string.
    Returns the date in standard YYYY-MM-DD format.
    Raises ValueError if the string can't be parsed as a date.
    Empty string is allowed (due dates are optional).

    With dateutil installed you can pass things like:
      "2025-12-31"
      "Dec 31 2025"
      "31 December 2025"
    Without dateutil only YYYY-MM-DD format works.
    """
    if not date_str:
        return date_str  # no date given, that's fine

    if _DATEUTIL_AVAILABLE:
        try:
            # dayfirst=False means "12/01/2025" is January 12th not December 1st
            # (American date format, not European)
            parsed = dateutil_parser.parse(date_str, dayfirst=False)
            return parsed.date().isoformat()  # always output as "YYYY-MM-DD"
        except (ValueError, OverflowError) as exc:
            raise ValueError(f"Cannot parse date '{date_str}': {exc}") from exc
    else:
        # fallback if dateutil somehow isn't installed
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        if not pattern.match(date_str):
            raise ValueError(
                f"Invalid date '{date_str}'. Expected YYYY-MM-DD format."
            )
        return date_str
