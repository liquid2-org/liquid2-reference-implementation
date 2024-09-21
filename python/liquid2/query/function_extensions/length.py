"""The standard `length` function extension."""

from collections.abc import Sized

from ..filter_expressions import NOTHING  # noqa: TID252
from ..filter_expressions import Nothing  # noqa: TID252
from ..function_extensions import ExpressionType  # noqa: TID252
from ..function_extensions import FilterFunction  # noqa: TID252


class Length(FilterFunction):
    """The standard `length` function."""

    arg_types = [ExpressionType.VALUE]
    return_type = ExpressionType.VALUE

    def __call__(self, obj: Sized) -> int | Nothing:
        """Return an object's length.

        If the object does not have a length, the special _Nothing_ value is
        returned.
        """
        try:
            return len(obj)
        except TypeError:
            return NOTHING
