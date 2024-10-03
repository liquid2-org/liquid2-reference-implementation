"""The standard _case_ tag."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import TextIO

from liquid2 import Markup
from liquid2 import Node
from liquid2 import Token
from liquid2.ast import BlockNode
from liquid2.ast import ConditionalBlockNode
from liquid2.builtin import BooleanExpression
from liquid2.builtin import EqExpression
from liquid2.builtin import LogicalOrExpression
from liquid2.builtin import parse_primitive
from liquid2.context import RenderContext
from liquid2.exceptions import LiquidSyntaxError
from liquid2.tag import Tag

if TYPE_CHECKING:
    from liquid2 import TokenT
    from liquid2.context import RenderContext
    from liquid2.expression import Expression
    from liquid2.tokens import TokenStream


class CaseNode(Node):
    """The standard _case_ tag."""

    __slots__ = ("whens", "default")

    def __init__(
        self,
        token: TokenT,
        whens: list[ConditionalBlockNode],
        default: BlockNode | None,
    ) -> None:
        super().__init__(token)
        self.whens = whens
        self.default = default

    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        """Render the node to the output buffer."""
        count = 0

        for when in self.whens:
            count += when.render(context, buffer)

        if not count and self.default is not None:
            count += self.default.render(context, buffer)

        return count

    async def render_to_output_async(
        self, context: RenderContext, buffer: TextIO
    ) -> int:
        """Render the node to the output buffer."""
        count = 0

        for when in self.whens:
            count += await when.render_async(context, buffer)

        if not count and self.default is not None:
            count += await self.default.render_async(context, buffer)

        return count


class CaseTag(Tag):
    """The standard _case_ tag."""

    block = True
    node_class = CaseNode
    end_block = frozenset(["endcase", "when", "else"])

    def parse(self, stream: TokenStream) -> Node:
        """Parse tokens from _stream_ into an AST node."""
        token = stream.current()
        assert isinstance(token, Markup.Tag)
        expr_stream = stream.into_inner()
        left = parse_primitive(expr_stream.next())
        expr_stream.expect_eos()

        # Check for content or markup between the _case_ tag and the first _when_ or
        # _else_ tag. It is not allowed.
        block_token = stream.current()
        match block_token:
            case Markup.Tag(name=name):
                if name not in self.end_block:
                    raise LiquidSyntaxError(
                        f"expected a 'when' tag, found '{name}'",
                        token=block_token,
                    )
            case Markup.Content(text=text):
                if not text.isspace():
                    raise LiquidSyntaxError(
                        "unexpected text after 'case' tag",
                        token=block_token,
                    )
                stream.next()
            case _:
                raise LiquidSyntaxError(
                    "unexpected markup after 'case' tag",
                    token=block_token,
                )

        whens: list[ConditionalBlockNode] = []
        default: BlockNode | None = None

        parse_block = self.env.parser.parse_block

        while stream.is_tag("when"):
            alternative_token = stream.current()
            assert isinstance(alternative_token, Markup.Tag)

            alternative_expression = self._parse_when_expression(
                left, stream.into_inner()
            )

            alternative_block = parse_block(stream, self.end_block)

            whens.append(
                ConditionalBlockNode(
                    alternative_token,
                    alternative_block,
                    alternative_expression,
                )
            )

        if stream.is_tag("else"):
            alternative_token = stream.next()
            assert isinstance(alternative_token, Markup.Tag)
            alternative_block = parse_block(stream, self.end_block)
            default = BlockNode(alternative_token, alternative_block)

        stream.expect_tag("endcase")

        return self.node_class(
            token,
            whens,
            default,
        )

    def _parse_when_expression(
        self, left: Expression, stream: TokenStream
    ) -> BooleanExpression:
        token = stream.next()
        assert token is not None

        expr: Expression = EqExpression(token, left, parse_primitive(token))

        if stream.current() is None:
            return BooleanExpression(token, expr)

        stream.expect_one_of(Token.Comma, Token.Or)
        stream.next()

        while True:
            or_token = stream.next()
            if or_token is None:
                break

            expr = LogicalOrExpression(
                or_token,
                expr,
                EqExpression(or_token, left, parse_primitive(or_token)),
            )

            if stream.current() is None:
                break

            stream.expect_one_of(Token.Comma, Token.Or)
            stream.next()

        stream.expect_eos()

        return BooleanExpression(token, expr)
