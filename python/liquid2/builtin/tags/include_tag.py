"""The standard _include_ tag."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import TextIO

from liquid2 import Markup
from liquid2 import Node
from liquid2 import Token
from liquid2.builtin import parse_primitive
from liquid2.builtin import parse_string_or_identifier
from liquid2.context import RenderContext
from liquid2.exceptions import LiquidSyntaxError
from liquid2.stringify import to_liquid_string
from liquid2.tag import Tag
from liquid2.tokens import TokenStream

if TYPE_CHECKING:
    from liquid2 import TokenT
    from liquid2.context import RenderContext
    from liquid2.expression import Expression


class IncludeNode(Node):
    """The standard _include_ tag."""

    __slots__ = ("name", "items", "cycle_hash")

    def __init__(
        self, token: TokenT, name: str | None, items: list[Expression]
    ) -> None:
        super().__init__(token)
        self.name = name
        self.items = tuple(items)
        self.cycle_hash = hash((self.name, self.items))

    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        """Render the node to the output buffer."""
        raise NotImplementedError

    async def render_to_output_async(
        self, context: RenderContext, buffer: TextIO
    ) -> int:
        """Render the node to the output buffer."""
        raise NotImplementedError


class IncludeTag(Tag):
    """The standard _include_ tag."""

    block = False
    node_class = IncludeNode

    def parse(self, stream: TokenStream) -> Node:
        """Parse tokens from _stream_ into an AST node."""
        token = stream.current()
        assert isinstance(token, Markup.Tag)

        raise NotImplementedError
