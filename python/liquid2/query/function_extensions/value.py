"""The standard `value` function extension."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..filter_expressions import NOTHING  # noqa: TID252
from ..function_extensions import ExpressionType  # noqa: TID252
from ..function_extensions import FilterFunction  # noqa: TID252

if TYPE_CHECKING:
    from ..node import JSONPathNodeList  # noqa: TID252


class Value(FilterFunction):
    """The standard `value` function."""

    arg_types = [ExpressionType.NODES]
    return_type = ExpressionType.VALUE

    def __call__(self, nodes: JSONPathNodeList) -> object:
        """Return the first node in a node list if it has only one item."""
        if len(nodes) == 1:
            return nodes[0].value
        return NOTHING
