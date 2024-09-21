"""Template abstract syntax tree."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import TextIO

from liquid2 import Node as ParseTreeNode
from liquid2.context import RenderContext

if TYPE_CHECKING:
    from liquid2 import FilteredExpression as IRFilteredExpression
    from liquid2 import Template as ParseTree

    from .context import RenderContext
    from .environment import Environment


class _AST:
    """Template abstract syntax tree."""

    def __init__(self, env: Environment, parse_tree: ParseTree) -> None:
        self.env = env
        self.nodes = self._make(parse_tree)

    def _make(self, parse_tree: ParseTree) -> list[_Node]:
        return [self._make_node(node) for node in parse_tree.liquid]

    def _make_node(self, node: ParseTreeNode) -> _Node:
        match node:
            case ParseTreeNode.Content():
                return _ContentNode(node)
            case ParseTreeNode.Output():
                return _OutputNode(node)
            # TODO:
        return _TodoNode()


class _Node(ABC):
    __slots__ = ()

    def render(self, render_context: RenderContext, buffer: TextIO) -> int:
        return self.render_to_output(render_context, buffer)

    @abstractmethod
    def render_to_output(self, render_context: RenderContext, buffer: TextIO) -> int:
        """Render the node to the output buffer.

        Return:
            The number of Unicode code points written to the output buffer.
        """


class _TodoNode(_Node):
    def render_to_output(self, render_context: RenderContext, buffer: TextIO) -> int:
        raise NotImplementedError(":(")


class _ContentNode(_Node):
    __slots__ = ("text",)

    def __init__(self, node: ParseTreeNode.Content) -> None:
        super().__init__()
        self.text = node.text

    def render_to_output(self, _render_context: RenderContext, buffer: TextIO) -> int:
        buffer.write(self.text)
        return len(self.text)


class _OutputNode(_Node):
    __slots__ = ("wc", "expression")

    def __init__(self, node: ParseTreeNode.Output) -> None:
        super().__init__()
        self.wc = node.wc
        self.expression = FilteredExpression(node.expression)

    def render_to_output(self, render_context: RenderContext, buffer: TextIO) -> int:
        # TODO
        raise NotImplementedError(":(")


class Expression(ABC):
    __slots__ = ()

    @abstractmethod
    def evaluate(self, render_context: RenderContext) -> object:
        """Evaluate the expression in the given render context."""

    # TODO: async
    # TODO: children


class FilteredExpression(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr: IRFilteredExpression) -> None:
        super().__init__()
        self._expr = expr

    def evaluate(self, render_context: RenderContext) -> object:
        # TODO
        raise NotImplementedError(":(")
