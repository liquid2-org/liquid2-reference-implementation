"""The built in, standard implementation of the _assign_ tag."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import TextIO

from liquid2 import Markup
from liquid2 import Node
from liquid2 import Token
from liquid2.builtin import FilteredExpression
from liquid2.builtin import parse_identifier
from liquid2.context import RenderContext
from liquid2.tag import Tag
from liquid2.tokens import TokenStream

if TYPE_CHECKING:
    from liquid2 import TokenT
    from liquid2.context import RenderContext
    from liquid2.expression import Expression


class AssignNode(Node):
    """The built in, standard implementation of the _assign_ node."""

    __slots__ = ("name", "expression")

    def __init__(self, token: TokenT, name: str, expression: Expression) -> None:
        super().__init__(token)
        self.name = name
        self.expression = expression

    def __str__(self) -> str:
        return f"{self.name} = {self.expression}"

    def render_to_output(self, context: RenderContext, _buffer: TextIO) -> int:
        """Render the node to the output buffer."""
        context.assign(self.name, self.expression.evaluate(context))
        return 0

    async def render_to_output_async(
        self, context: RenderContext, _buffer: TextIO
    ) -> int:
        """Render the node to the output buffer."""
        context.assign(self.name, await self.expression.evaluate_async(context))
        return 0


class AssignTag(Tag):
    """The standard _assign_ tag."""

    block = False
    node_class = AssignNode

    def parse(self, stream: TokenStream) -> Node:
        """Parse tokens from _stream_ into an AST node."""
        token = stream.current()
        assert isinstance(token, Markup.Tag)

        expr_stream = TokenStream(token.expression)
        name = parse_identifier(next(expr_stream, None))
        expr_stream.expect(Token.Assign)
        next(expr_stream)

        return self.node_class(
            token, name=name, expression=FilteredExpression.parse(expr_stream)
        )
