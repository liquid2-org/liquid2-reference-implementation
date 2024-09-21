"""Manage undefined template variables.

When rendering a Liquid template, if a variable name can not be resolved, an instance of
liquid.Undefined, or a subclass, is used instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Iterable
from typing import Iterator
from typing import Mapping

from .exceptions import UndefinedError

if TYPE_CHECKING:
    from .query import Query

UNDEFINED = object()


class Undefined(Mapping[Any, object]):
    """The default undefined type.

    Always evaluates to an empty string. Can be iterated over and indexed without error.
    """

    __slots__ = ("path", "obj", "hint")

    def __init__(self, path: Query, obj: object = UNDEFINED, hint: str | None = None):
        self.path = path
        self.obj = obj
        self.hint = hint

    def __contains__(self, item: object) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Undefined) or other is None

    def __getitem__(self, key: str) -> object:
        return self

    def __len__(self) -> int:
        return 0

    def __iter__(self) -> Iterator[Any]:
        return iter([])

    def __str__(self) -> str:
        return ""

    def __repr__(self) -> str:  # pragma: no cover
        return f"Undefined({self.path})"

    def __int__(self) -> int:
        return 0

    def __hash__(self) -> int:
        return hash(self.path)

    def __reversed__(self) -> Iterable[Any]:
        return []


class DebugUndefined(Undefined):
    """An undefined that returns debug information when rendered."""

    __slots__ = ()

    def __str__(self) -> str:
        if self.hint:
            return f"undefined: {self.hint}"
        if self.obj is not UNDEFINED:
            return f"{type(self.obj).__name__} has no attribute '{self.path}'"
        return f"'{self.path}' is undefined"

    def __repr__(self) -> str:  # pragma: no cover
        return f"Undefined({self.path})"


class StrictUndefined(Undefined):
    """An undefined that raises an exception for everything other than `repr`."""

    __slots__ = ("msg",)

    # Properties that don't raise an UndefinedError.
    allowed_properties = frozenset(
        [
            "__repr__",
            "name",
            "hint",
            "obj",
            "msg",
        ]
    )

    def __init__(self, path: Query, obj: object = UNDEFINED, hint: str | None = None):
        super().__init__(path, obj=obj, hint=hint)
        self.msg = self.hint if self.hint else f"'{self.path}' is undefined"

    def __getattribute__(self, name: str) -> object:
        if name in object.__getattribute__(self, "allowed_properties"):
            return object.__getattribute__(self, name)
        raise UndefinedError(object.__getattribute__(self, "msg"))

    def __contains__(self, item: object) -> bool:
        raise UndefinedError(self.msg)

    def __eq__(self, other: object) -> bool:
        raise UndefinedError(self.msg)

    def __getitem__(self, key: str) -> object:
        raise UndefinedError(self.msg)

    def __len__(self) -> int:
        raise UndefinedError(self.msg)

    def __iter__(self) -> Iterator[Any]:
        raise UndefinedError(self.msg)

    def __str__(self) -> str:
        raise UndefinedError(self.msg)

    def __repr__(self) -> str:
        return f"StrictUndefined({self.path})"

    def __bool__(self) -> bool:
        raise UndefinedError(self.msg)

    def __int__(self) -> int:
        raise UndefinedError(self.msg)

    def __hash__(self) -> int:
        raise UndefinedError(self.msg)

    def __reversed__(self) -> Iterable[Any]:
        raise UndefinedError(self.msg)


class StrictDefaultUndefined(StrictUndefined):
    """An undefined that plays nicely with the `default` filter."""

    # Force the `default` filter to return its default value
    # without inspecting this class type.
    force_liquid_default = True

    # Properties that don't raise an UndefinedError.
    allowed_properties = frozenset(
        [
            "__repr__",
            "force_liquid_default",
            "name",
            "hint",
            "obj",
            "msg",
        ]
    )


def is_undefined(obj: object) -> bool:
    """Return `True` if `obj` is undefined. `False` otherwise."""
    return isinstance(obj, Undefined)
