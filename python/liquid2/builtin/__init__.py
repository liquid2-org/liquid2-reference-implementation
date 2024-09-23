"""Filters, tags and expressions built-in to Liquid."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._expressions import BLANK
from ._expressions import CONTINUE
from ._expressions import EMPTY
from ._expressions import FALSE
from ._expressions import NULL
from ._expressions import TRUE
from ._expressions import Blank
from ._expressions import Boolean
from ._expressions import BooleanExpression
from ._expressions import Continue
from ._expressions import Empty
from ._expressions import Filter
from ._expressions import FilteredExpression
from ._expressions import FloatLiteral
from ._expressions import IntegerLiteral
from ._expressions import KeywordArgument
from ._expressions import Literal
from ._expressions import LogicalAndExpression
from ._expressions import LogicalNotExpression
from ._expressions import LogicalOrExpression
from ._expressions import Null
from ._expressions import PositionalArgument
from ._expressions import Query
from ._expressions import RangeLiteral
from ._expressions import StringLiteral
from ._expressions import SymbolArgument
from ._expressions import TernaryFilteredExpression

# TODO: export more expressions
from .filters.array import compact
from .filters.array import concat
from .filters.array import first
from .filters.array import join
from .filters.array import last
from .filters.array import map_
from .filters.array import reverse
from .filters.array import sort
from .filters.array import sort_natural
from .filters.array import sum_
from .filters.array import uniq
from .filters.array import where
from .filters.string import append
from .filters.string import capitalize
from .filters.string import downcase
from .filters.string import escape
from .filters.string import escape_once
from .filters.string import lstrip
from .filters.string import newline_to_br
from .filters.string import prepend
from .filters.string import remove
from .filters.string import remove_first
from .filters.string import remove_last
from .filters.string import replace
from .filters.string import replace_first
from .filters.string import replace_last
from .filters.string import rstrip
from .filters.string import slice_
from .filters.string import split
from .filters.string import strip
from .filters.string import strip_html
from .filters.string import strip_newlines
from .filters.string import truncate
from .filters.string import truncatewords
from .filters.string import upcase
from .filters.string import url_decode
from .filters.string import url_encode

if TYPE_CHECKING:
    from ..environment import Environment  # noqa: TID252

__all__ = (
    "Blank",
    "BLANK",
    "Boolean",
    "BooleanExpression",
    "Continue",
    "CONTINUE",
    "Empty",
    "EMPTY",
    "FALSE",
    "Filter",
    "FilteredExpression",
    "FilteredExpression",
    "FloatLiteral",
    "IntegerLiteral",
    "KeywordArgument",
    "Literal",
    "LogicalAndExpression",
    "LogicalNotExpression",
    "LogicalOrExpression",
    "Null",
    "NULL",
    "PositionalArgument",
    "Query",
    "RangeLiteral",
    "register_standard_tags_and_filters",
    "StringLiteral",
    "SymbolArgument",
    "TernaryFilteredExpression",
    "TRUE",
)


def register_standard_tags_and_filters(env: Environment) -> None:
    """Register standard tags and filters with an environment."""
    env.filters["join"] = join
    env.filters["first"] = first
    env.filters["last"] = last
    env.filters["concat"] = concat
    env.filters["map"] = map_
    env.filters["reverse"] = reverse
    env.filters["sort"] = sort
    env.filters["sort_natural"] = sort_natural
    env.filters["sum"] = sum_
    env.filters["where"] = where
    env.filters["uniq"] = uniq
    env.filters["compact"] = compact

    env.filters["capitalize"] = capitalize
    env.filters["append"] = append
    env.filters["downcase"] = downcase
    env.filters["escape"] = escape
    env.filters["escape_once"] = escape_once
    env.filters["lstrip"] = lstrip
    env.filters["newline_to_br"] = newline_to_br
    env.filters["prepend"] = prepend
    env.filters["remove"] = remove
    env.filters["remove_first"] = remove_first
    env.filters["remove_last"] = remove_last
    env.filters["replace"] = replace
    env.filters["replace_first"] = replace_first
    env.filters["replace_last"] = replace_last
    env.filters["slice"] = slice_
    env.filters["split"] = split
    env.filters["upcase"] = upcase
    env.filters["strip"] = strip
    env.filters["rstrip"] = rstrip
    env.filters["strip_html"] = strip_html
    env.filters["strip_newlines"] = strip_newlines
    env.filters["truncate"] = truncate
    env.filters["truncatewords"] = truncatewords
    env.filters["url_encode"] = url_encode
    env.filters["url_decode"] = url_decode
