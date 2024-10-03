"""The standard _decrement_ tag."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import TextIO

from liquid2 import Markup
from liquid2 import Node
from liquid2.builtin import parse_string_or_identifier
from liquid2.exceptions import LiquidSyntaxError
from liquid2.tag import Tag
from liquid2.tokens import TokenStream

if TYPE_CHECKING:
    from liquid2 import TokenT
    from liquid2.context import RenderContext


class DecrementNode(Node):
    """The standard _decrement_ tag."""

    __slots__ = ("name", "name")

    def __init__(self, token: TokenT, name: str) -> None:
        super().__init__(token)
        self.name = name

    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        """Render the node to the output buffer."""
        return buffer.write(str(context.decrement(self.name)))


class DecrementTag(Tag):
    """The standard _decrement_ tag."""

    block = False
    node_class = DecrementNode

    def parse(self, stream: TokenStream) -> Node:
        """Parse tokens from _stream_ into an AST node."""
        token = stream.current()
        assert isinstance(token, Markup.Tag)

        if not token.expression:
            raise LiquidSyntaxError("expected an identifier", token=token)

        expr_stream = TokenStream(token.expression)
        name = parse_string_or_identifier(next(expr_stream, None))
        expr_stream.expect_eos()
        return self.node_class(token, name)
