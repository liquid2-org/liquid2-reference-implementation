"""Template render context."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from typing import Iterator
from typing import Mapping

from .chainmap import ReadOnlyChainMap
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
        "namespace",
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
        self.namespace = ReadOnlyChainMap(
            self.locals,
            self.globals,
            builtin,
            self.counters,
        )

    def get(self, path: Query, default: object = UNDEFINED) -> object:
        """Resolve the variable _path_ in the current namespace."""
        nodes = path.find(self.namespace)

        if not nodes:
            if default == UNDEFINED:
                return self.template.env.undefined(path)
            return default

        if len(nodes) == 1:
            return nodes[0].value

        return nodes


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
