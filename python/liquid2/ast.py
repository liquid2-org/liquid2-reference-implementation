"""Base class for all template nodes."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import TextIO

from liquid2.context import RenderContext

if TYPE_CHECKING:
    from _liquid2 import TokenT

    from .builtin import BooleanExpression
    from .context import RenderContext


class Node(ABC):
    """Base class for all template nodes."""

    __slots__ = ("token",)

    def __init__(self, token: TokenT) -> None:
        super().__init__()
        self.token = token

    def render(self, context: RenderContext, buffer: TextIO) -> int:
        """Write this node's content to _buffer_."""
        # TODO: disabled tags
        return self.render_to_output(context, buffer)

    async def render_async(self, context: RenderContext, buffer: TextIO) -> int:
        """Write this node's content to _buffer_."""
        # TODO: disabled tags
        return await self.render_to_output_async(context, buffer)

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


class BlockNode(Node):
    """A node containing a sequence of other nodes."""

    __slots__ = ("nodes",)

    def __init__(self, token: TokenT, nodes: list[Node]) -> None:
        super().__init__(token)
        self.nodes = nodes

    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        """Render the node to the output buffer."""
        return sum(node.render(context, buffer) for node in self.nodes)

    async def render_to_output_async(
        self, context: RenderContext, buffer: TextIO
    ) -> int:
        """Render the node to the output buffer."""
        return sum([await node.render_async(context, buffer) for node in self.nodes])


class ConditionalBlockNode(Node):
    """A node containing a sequence of other nodes guarded by a Boolean expression."""

    __slots__ = ("nodes", "expression")

    def __init__(
        self,
        token: TokenT,
        nodes: list[Node],
        expression: BooleanExpression,
    ) -> None:
        super().__init__(token)
        self.nodes = nodes
        self.expression = expression

    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        """Render the node to the output buffer."""
        if self.expression.evaluate(context):
            return sum(node.render(context, buffer) for node in self.nodes)
        return 0

    async def render_to_output_async(
        self, context: RenderContext, buffer: TextIO
    ) -> int:
        """Render the node to the output buffer."""
        if await self.expression.evaluate_async(context):
            return sum(
                [await node.render_async(context, buffer) for node in self.nodes]
            )
        return 0
