"""The built in, standard implementation of the text content node."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import TextIO

from liquid2 import Markup
from liquid2 import Node
from liquid2 import Whitespace
from liquid2.tag import Tag

if TYPE_CHECKING:
    from liquid2 import TokenT
    from liquid2.context import RenderContext
    from liquid2.tokens import TokenStream


class ContentNode(Node):
    """The built in, standard implementation of the text content node."""

    __slots__ = ("text",)

    def __init__(self, token: TokenT, text: str) -> None:
        super().__init__(token)
        self.text = text

    def __str__(self) -> str:
        return self.text

    def render_to_output(self, _context: RenderContext, buffer: TextIO) -> int:
        """Render the node to the output buffer."""
        return buffer.write(self.text)


class Content(Tag):
    """The template text content pseudo tag."""

    block = False
    node_class = ContentNode

    def parse(
        self,
        stream: TokenStream,
        *,
        left_trim: Whitespace = Whitespace.Default,
    ) -> Node:
        """Parse tokens from _stream_ into an AST node."""
        token = stream.current()
        assert isinstance(token, Markup.Content)

        peeked = stream.peek()

        right_trim = (
            peeked.wc[0]  # type: ignore
            if peeked is not None and not isinstance(peeked, Markup.EOI)
            else self.env.trim
        )

        return self.node_class(token, self.trim(token.text, left_trim, right_trim))

    def trim(self, text: str, left_trim: Whitespace, right_trim: Whitespace) -> str:  # noqa: PLR0911
        """Return text after applying whitespace control."""
        match (left_trim, right_trim):
            case (Whitespace.Default, Whitespace.Default):
                return self.trim(text, self.env.trim, self.env.trim)
            case (Whitespace.Default, _):
                return self.trim(text, self.env.trim, right_trim)
            case (_, Whitespace.Default):
                return self.trim(text, left_trim, self.env.trim)

            case (Whitespace.Minus, Whitespace.Minus):
                return text.strip()
            case (Whitespace.Minus, Whitespace.Plus):
                return text.lstrip()
            case (Whitespace.Plus, Whitespace.Minus):
                return text.rstrip()
            case (Whitespace.Plus, Whitespace.Plus):
                return text

            case (Whitespace.Smart, Whitespace.Smart):
                return text.strip("\r\n")
            case (Whitespace.Smart, right):
                return self.trim(text.lstrip("\r\n"), Whitespace.Plus, right)
            case (left, Whitespace.Smart):
                return self.trim(text.rstrip("\r\n"), left, Whitespace.Plus)
            case _:
                return text
