"""Stringify a Python object ready for output in a Liquid template."""

from typing import Any

from markupsafe import Markup
from markupsafe import escape
from markupsafe import soft_str


def to_liquid_string(val: Any, auto_escape: bool) -> str:
    """Stringify a Python object ready for output in a Liquid template."""
    if isinstance(val, str) or (auto_escape and hasattr(val, "__html__")):
        pass
    elif isinstance(val, bool):
        val = str(val).lower()
    elif val is None:
        val = ""
    elif isinstance(val, list):
        if auto_escape:
            val = Markup("").join(soft_str(itm) for itm in val)
        else:
            val = "".join(soft_str(itm) for itm in val)
    elif isinstance(val, range):
        val = f"{val.start}..{val.stop - 1}"
    else:
        val = str(val)

    if auto_escape:
        val = escape(val)

    assert isinstance(val, str)
    return val
