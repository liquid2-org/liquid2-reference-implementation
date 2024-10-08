"""JSONPath child and descendant segment definitions."""

from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Iterable

from .exceptions import JSONPathRecursionError
from .selectors import NameSelector
from .selectors import WildcardSelector

if TYPE_CHECKING:
    from liquid2 import TokenT

    from .environment import _JSONPathEnvironment
    from .node import JSONPathNode
    from .selectors import JSONPathSelector


RE_SHORTHAND_NAME = re.compile(r"[\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*")


class JSONPathSegment(ABC):
    """Base class for all JSONPath segments."""

    __slots__ = ("env", "token", "selectors")

    def __init__(
        self,
        *,
        env: _JSONPathEnvironment,
        token: TokenT,
        selectors: tuple[JSONPathSelector, ...],
    ) -> None:
        self.env = env
        self.token = token
        self.selectors = selectors

    @abstractmethod
    def resolve(self, nodes: Iterable[JSONPathNode]) -> Iterable[JSONPathNode]:
        """Apply this segment to each `JSONPathNode` in _nodes_."""


class JSONPathChildSegment(JSONPathSegment):
    """The JSONPath child selection segment."""

    def resolve(self, nodes: Iterable[JSONPathNode]) -> Iterable[JSONPathNode]:
        """Select children of each node in _nodes_."""
        for node in nodes:
            for selector in self.selectors:
                yield from selector.resolve(node)

    def __str__(self) -> str:
        # Shorthand name?
        if len(self.selectors) == 1:
            match self.selectors[0]:
                case NameSelector(name=name):
                    if RE_SHORTHAND_NAME.fullmatch(name):
                        return f".{name}"
                    return f"['{name}']"
                case WildcardSelector():
                    return ".*"

        return f"[{', '.join(str(itm) for itm in self.selectors)}]"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, JSONPathChildSegment)
            and self.selectors == __value.selectors
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash(self.selectors)


class JSONPathRecursiveDescentSegment(JSONPathSegment):
    """The JSONPath recursive descent segment."""

    def resolve(self, nodes: Iterable[JSONPathNode]) -> Iterable[JSONPathNode]:
        """Select descendants of each node in _nodes_."""
        for node in nodes:
            for _node in self._visit(node):
                for selector in self.selectors:
                    yield from selector.resolve(_node)

    def _visit(self, node: JSONPathNode, depth: int = 1) -> Iterable[JSONPathNode]:
        """Depth-first, pre-order node traversal."""
        if depth > self.env.max_recursion_depth:
            raise JSONPathRecursionError("recursion limit exceeded", token=self.token)

        yield node

        if isinstance(node.value, dict):
            for name, val in node.value.items():
                if isinstance(val, (dict, list)):
                    _node = node.new_child(val, name)
                    yield from self._visit(_node, depth + 1)
        elif isinstance(node.value, list):
            for i, element in enumerate(node.value):
                if isinstance(element, (dict, list)):
                    _node = node.new_child(element, i)
                    yield from self._visit(_node, depth + 1)

    def __str__(self) -> str:
        if len(self.selectors) == 1:
            match self.selectors[0]:
                case NameSelector(name=name):
                    return f"..{name}"
                case WildcardSelector():
                    return "..*"

        return f"..[{', '.join(str(itm) for itm in self.selectors)}]"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, JSONPathRecursiveDescentSegment)
            and self.selectors == __value.selectors
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash(("..", self.selectors, self.token))
