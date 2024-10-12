"""Filter function helpers."""

from __future__ import annotations

from decimal import Decimal
from functools import wraps
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Iterator

from markupsafe import soft_str

from .exceptions import FilterArgumentError
from .limits import to_int


def with_context(_filter: Callable[..., Any]) -> Callable[..., Any]:
    """Pass the active render context to decorated filter functions.

    If a function is decorated with `with_context`, that function should
    accept a `context` keyword argument, being the active render context.

    Args:
        _filter: The filter function to decorate.
    """
    _filter.with_context = True  # type: ignore
    return _filter


def with_environment(_filter: Callable[..., Any]) -> Callable[..., Any]:
    """Pass the active environment to decorated filter functions.

    If a function is decorated with `with_environment`, that function should
    accept an `environment` keyword argument, being the active environment.

    Args:
        _filter: The filter function to decorate.
    """
    _filter.with_environment = True  # type: ignore
    return _filter


def to_string(obj: object) -> str:
    """Return a string representation of _obj_.

    This function is safe to use on markupsafe.Markup.
    """
    return soft_str(obj)


def string_filter(_filter: Callable[..., Any]) -> Callable[..., Any]:
    """A filter function decorator that converts the first argument to a string."""

    @wraps(_filter)
    def wrapper(val: object, *args: Any, **kwargs: Any) -> Any:
        try:
            return _filter(to_string(val), *args, **kwargs)
        except TypeError as err:
            raise FilterArgumentError(err) from err

    return wrapper


def sequence_filter(_filter: Callable[..., Any]) -> Callable[..., Any]:
    """Coerce the left value to sequence.

    This is intended to mimic the semantics of the reference implementation's
    `InputIterator` class.
    """

    @wraps(_filter)
    def wrapper(val: object, *args: Any, **kwargs: Any) -> Any:
        if isinstance(val, (list, tuple)):
            val = flatten(val)
        elif isinstance(val, (dict, str)) or not isinstance(val, Iterable):
            val = [val]

        try:
            return _filter(val, *args, **kwargs)
        except TypeError as err:
            raise FilterArgumentError(err) from err

    return wrapper


def liquid_filter(_filter: Callable[..., Any]) -> Callable[..., Any]:
    """A filter function decorator that wraps `TypeError` in `FilterArgumentError`."""

    @wraps(_filter)
    def wrapper(val: object, *args: Any, **kwargs: Any) -> Any:
        try:
            return _filter(val, *args, **kwargs)
        except TypeError as err:
            raise FilterArgumentError(err) from err

    return wrapper


def int_arg(val: Any, default: int | None = None) -> int:
    """Return `val` as an int or `default` if `val` can't be cast to an int."""
    try:
        return to_int(val)
    except ValueError as err:
        if default is not None:
            return default
        raise FilterArgumentError(
            f"expected an int or string, found {type(val).__name__}"
        ) from err


def num_arg(
    val: Any, default: float | int | Decimal | None = None
) -> float | int | Decimal:
    """Return `val` as an int or float.

    If `val` can't be cast to an int or float, return `default`.
    """
    if isinstance(val, (int, float)):
        return val

    if isinstance(val, str):
        try:
            return to_int(val)
        except ValueError:
            pass

        try:
            return float(val)
        except ValueError as err:
            if default is not None:
                return default
            raise FilterArgumentError(
                f"could not cast string '{val}' to a number"
            ) from err

    elif default is not None:
        return default

    raise FilterArgumentError(
        f"expected an int, float or string, found {type(val).__name__}"
    )


def decimal_arg(val: Any, default: int | Decimal | None = None) -> int | Decimal:
    """Return `val` as an int or decimal.

    If `val` can't be cast to an int or decimal, return `default`.
    """
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return Decimal(str(val))

    if isinstance(val, str):
        try:
            return to_int(val)
        except ValueError:
            pass

        try:
            return Decimal(val)
        except ValueError as err:
            if default is not None:
                return default
            raise FilterArgumentError(
                f"could not cast string '{val}' to a number"
            ) from err

    elif default is not None:
        return default

    raise FilterArgumentError(
        f"expected an int, float or string, found {type(val).__name__}"
    )


def math_filter(_filter: Callable[..., Any]) -> Callable[..., Any]:
    """Raise a `FilterArgumentError` if the filter value can not be a number."""

    @wraps(_filter)
    def wrapper(val: object, *args: Any, **kwargs: Any) -> Any:
        val = num_arg(val, default=0)

        try:
            return _filter(val, *args, **kwargs)
        except TypeError as err:
            raise FilterArgumentError(err) from err

    return wrapper


def flatten(it: Iterable[Any], level: int = 5) -> list[object]:
    """Flatten nested "liquid arrays" into a list."""

    def _flatten(it: Iterable[Any], level: int = 5) -> Iterator[object]:
        for obj in it:
            if not level or not isinstance(obj, (list, tuple)):
                yield obj
            else:
                yield from _flatten(obj, level=level - 1)

    return list(_flatten(it, level))
