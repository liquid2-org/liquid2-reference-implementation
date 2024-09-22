"""Template render context."""

from __future__ import annotations

import datetime
from contextlib import contextmanager
from functools import partial
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Iterator
from typing import Mapping

from .chainmap import ReadOnlyChainMap
from .exceptions import ContextDepthError
from .exceptions import NoSuchFilterFunc
from .undefined import UNDEFINED

if TYPE_CHECKING:
    from .query import Query
    from .template import Template


class RenderContext:
    """Template render state."""

    __slots__ = (
        "template",
        "globals",
        "disabled_tags",
        "parent",
        "copy_depth",
        "loop_iteration_carry",
        "local_namespace_carry",
        "locals",
        "counters",
        "scope",
        "auto_escape",
        "env",
    )

    def __init__(
        self,
        template: Template,
        *,
        global_data: Mapping[str, object] | None = None,
        disabled_tags: list[str] | None = None,
        parent: RenderContext | None = None,
        copy_depth: int = 0,
        loop_iteration_carry: int = 1,
        local_namespace_carry: int = 0,
    ) -> None:
        self.template = template
        self.globals = global_data or {}
        self.disabled_tags = disabled_tags or []
        self.parent = parent
        self.copy_depth = copy_depth
        self.loop_iteration_carry = loop_iteration_carry
        self.local_namespace_carry = local_namespace_carry

        self.locals: dict[str, int] = {}
        self.counters: dict[str, int] = {}
        self.scope = ReadOnlyChainMap(
            self.locals,
            self.globals,
            builtin,
            self.counters,
        )

        self.env = template.env
        self.auto_escape = self.env.auto_escape

    def get(self, path: Query, default: object = UNDEFINED) -> object:
        """Resolve the variable _path_ in the current namespace."""
        nodes = path.find(self.scope)

        if not nodes:
            if default == UNDEFINED:
                return self.template.env.undefined(path)
            return default

        if len(nodes) == 1:
            return nodes[0].value

        return nodes

    def filter(self, name: str) -> Callable[..., object]:
        """Return the filter callable for _name_."""
        try:
            filter_func = self.env.filters[name]
        except KeyError as err:
            raise NoSuchFilterFunc(f"unknown filter '{name}'") from err

        kwargs: dict[str, Any] = {}

        if getattr(filter_func, "with_context", False):
            kwargs["context"] = self

        if getattr(filter_func, "with_environment", False):
            kwargs["environment"] = self.env

        if kwargs:
            if hasattr(filter_func, "filter_async"):
                _filter_func = partial(filter_func, **kwargs)
                _filter_func.filter_async = partial(  # type: ignore
                    filter_func.filter_async,
                    **kwargs,
                )
                return _filter_func
            return partial(filter_func, **kwargs)

        return filter_func

    @contextmanager
    def extend(
        self, namespace: Mapping[str, object], template: Template | None = None
    ) -> Iterator[RenderContext]:
        """Extend this context with the given read-only namespace."""
        if self.scope.size() > self.env.context_depth_limit:
            raise ContextDepthError(
                "maximum context depth reached, possible recursive include"
            )

        _template = self.template
        if template:
            self.template = template

        self.scope.push(namespace)

        try:
            yield self
        finally:
            if template:
                self.template = _template
            self.scope.pop()


class BuiltIn(Mapping[str, object]):
    """Mapping-like object for resolving built-in, dynamic objects."""

    def __contains__(self, item: object) -> bool:
        return item in ("now", "today")

    def __getitem__(self, key: str) -> object:
        if key == "now":
            return datetime.datetime.now()
        if key == "today":
            return datetime.date.today()
        raise KeyError(str(key))

    def __len__(self) -> int:
        return 2

    def __iter__(self) -> Iterator[str]:
        return iter(["now", "today"])


builtin = BuiltIn()
