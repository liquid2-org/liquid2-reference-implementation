"""The built in, standard implementation of the output statement."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import TextIO

from liquid2 import Markup
from liquid2 import Node
from liquid2.builtin import FilteredExpression
from liquid2.context import RenderContext
from liquid2.stringify import to_liquid_string
from liquid2.tag import Tag
from liquid2.tokens import TokenStream

if TYPE_CHECKING:
    from liquid2 import TokenT
    from liquid2.context import RenderContext
    from liquid2.expression import Expression
    from liquid2.tokens import TokenStream


class OutputNode(Node):
    """The built in, standard implementation of the output statement."""

    __slots__ = ("expression",)

    def __init__(self, token: TokenT, expression: Expression) -> None:
        super().__init__(token)
        self.expression = expression

    def __str__(self) -> str:
        return f"`{self.expression}`"

    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        """Render the node to the output buffer."""
        return buffer.write(
            to_liquid_string(
                self.expression.evaluate(context),
                context.auto_escape,
            )
        )

    async def render_to_output_async(
        self, context: RenderContext, buffer: TextIO
    ) -> int:
        """Render the node to the output buffer."""
        return buffer.write(
            to_liquid_string(
                await self.expression.evaluate_async(context),
                auto_escape=context.auto_escape,
            )
        )


class Output(Tag):
    """The built in pseudo tag for output statements."""

    block = False
    node_class = OutputNode

    def parse(self, stream: TokenStream) -> Node:
        """Parse tokens from _stream_ into an AST node."""
        token = stream.current
        assert isinstance(token, Markup.Output)
        return self.node_class(token, FilteredExpression.parse(token.expression))
