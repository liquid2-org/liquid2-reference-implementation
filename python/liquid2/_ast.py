"""Template abstract syntax tree."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import TextIO

from _liquid2 import Node as ParseTreeNode
from _liquid2 import WhitespaceControl

from .builtin import FilteredExpression
from .builtin import TernaryFilteredExpression
from .context import RenderContext
from .stringify import to_liquid_string

if TYPE_CHECKING:
    from _liquid2 import FilteredExpression as IRFilteredExpression
    from _liquid2 import Template as ParseTree

    from .context import RenderContext
    from .environment import Environment


class AST:
    """Template abstract syntax tree."""

    def __init__(self, env: Environment, parse_tree: ParseTree) -> None:
        self.env = env
        self.nodes = self._make(parse_tree)

    def _make(self, parse_tree: ParseTree) -> list[Node]:
        return [self._make_node(node) for node in parse_tree.liquid]

    def _make_node(self, node: ParseTreeNode) -> Node:
        trim = self.env.trim
        lstrip = trim
        match node:
            case ParseTreeNode.Content():
                # TODO: trim
                return ContentNode(node)
            case ParseTreeNode.Output():
                return OutputNode(node)
            case ParseTreeNode.Raw():
                return RawNode(node)
            case ParseTreeNode.Comment():
                return CommentNode(node)
            case ParseTreeNode.AssignTag():
                return AssignNode(node)
            # TODO:
        return _TodoNode(None)


def render_block(nodes: list[Node], context: RenderContext, buffer: TextIO) -> int:
    return sum(node.render(context, buffer) for node in nodes)


class Node(ABC):
    __slots__ = ("wc",)

    __match_args__ = ("wc",)

    def __init__(
        self, wc: WhitespaceControl | tuple[WhitespaceControl, WhitespaceControl] | None
    ) -> None:
        super().__init__()
        self.wc = wc

    def render(self, context: RenderContext, buffer: TextIO) -> int:
        return self.render_to_output(context, buffer)

    @abstractmethod
    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        """Render the node to the output buffer.

        Return:
            The number of "characters" written to the output buffer.
        """

    async def render_to_output_async(
        self, context: RenderContext, buffer: TextIO
    ) -> int:
        """An async version of _render_to_output_."""
        return self.render_to_output(context, buffer)


class _TodoNode(Node):
    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        raise NotImplementedError(":(")


class ContentNode(Node):
    __slots__ = (
        "wc",
        "text",
    )

    def __init__(self, node: ParseTreeNode.Content) -> None:
        self.wc = None
        self.text = node.text

    def render_to_output(self, _context: RenderContext, buffer: TextIO) -> int:
        return buffer.write(self.text)


def _filtered_expression(
    node: IRFilteredExpression,
) -> FilteredExpression | TernaryFilteredExpression:
    expr = FilteredExpression(node)
    if node.condition:
        return TernaryFilteredExpression(expr, node.condition)
    return expr


class OutputNode(Node):
    __slots__ = ("wc", "expression")

    def __init__(self, node: ParseTreeNode.Output) -> None:
        self.wc = node.wc
        self.expression = _filtered_expression(node.expression)

    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        return buffer.write(
            to_liquid_string(self.expression.evaluate(context), context.auto_escape)
        )

    async def render_to_output_async(
        self, context: RenderContext, buffer: TextIO
    ) -> int:
        return buffer.write(
            to_liquid_string(
                await self.expression.evaluate_async(context), context.auto_escape
            )
        )


class RawNode(Node):
    __slots__ = ("wc", "text")

    def __init__(self, node: ParseTreeNode.Raw) -> None:
        self.wc = node.wc
        self.text = node.text

    def render_to_output(self, _context: RenderContext, buffer: TextIO) -> int:
        return buffer.write(self.text)


class CommentNode(Node):
    __slots__ = ("wc", "text")

    def __init__(self, node: ParseTreeNode.Comment) -> None:
        self.wc = node.wc
        self.text = node.text

    def render_to_output(self, _context: RenderContext, _buffer: TextIO) -> int:
        return 0


class AssignNode(Node):
    __slots__ = ("wc", "identifier", "expression")

    def __init__(self, node: ParseTreeNode.AssignTag) -> None:
        self.wc = node.wc
        self.identifier = node.identifier
        self.expression = _filtered_expression(node.expression)

    def render_to_output(self, context: RenderContext, _buffer: TextIO) -> int:
        context.assign(self.identifier, self.expression.evaluate(context))
        return 0

    async def render_to_output_async(
        self, context: RenderContext, _buffer: TextIO
    ) -> int:
        context.assign(self.identifier, await self.expression.evaluate_async(context))
        return 0
