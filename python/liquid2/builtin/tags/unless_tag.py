"""The standard _unless_ tag."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import TextIO

from liquid2 import Markup
from liquid2 import Node
from liquid2.ast import BlockNode
from liquid2.ast import ConditionalBlockNode
from liquid2.builtin import BooleanExpression
from liquid2.context import RenderContext
from liquid2.tag import Tag
from liquid2.tokens import TokenStream

if TYPE_CHECKING:
    from liquid2 import TokenT
    from liquid2.context import RenderContext


class UnlessNode(Node):
    """The standard _unless_ tag."""

    __slots__ = ("condition", "consequence", "alternatives", "alternative")

    def __init__(
        self,
        token: TokenT,
        condition: BooleanExpression,
        consequence: BlockNode,
        alternatives: list[ConditionalBlockNode],
        alternative: BlockNode | None,
    ) -> None:
        super().__init__(token)
        self.condition = condition
        self.consequence = consequence
        self.alternatives = alternatives
        self.alternative = alternative

    def __str__(self) -> str:
        buf = [
            f"unless {self.condition} {{ {self.consequence} }}",
        ]

        for alt in self.alternatives:
            buf.append(f"elsif {alt}")

        if self.alternative:
            buf.append(f"else {{ {self.alternative} }}")
        return " ".join(buf)

    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        """Render the node to the output buffer."""
        if not self.condition.evaluate(context):
            return self.consequence.render(context, buffer)

        for alternative in self.alternatives:
            if alternative.expression.evaluate(context):
                return sum(node.render(context, buffer) for node in alternative.nodes)

        if self.alternative:
            return self.alternative.render(context, buffer)

        return 0

    async def render_to_output_async(
        self, context: RenderContext, buffer: TextIO
    ) -> int:
        """Render the node to the output buffer."""
        if not await self.condition.evaluate_async(context):
            return await self.consequence.render_async(context, buffer)

        for alternative in self.alternatives:
            if await alternative.expression.evaluate_async(context):
                return sum(
                    [
                        await node.render_async(context, buffer)
                        for node in alternative.nodes
                    ]
                )

        if self.alternative:
            return await self.alternative.render_async(context, buffer)

        return 0


class UnlessTag(Tag):
    """The standard _unless_ tag."""

    block = False
    node_class = UnlessNode
    end_block = frozenset(["endunless", "elsif", "else"])

    def parse(self, stream: TokenStream) -> Node:
        """Parse tokens from _stream_ into an AST node."""
        token = next(stream)
        assert isinstance(token, Markup.Tag)

        parse_block = self.env.parser.parse_block
        parse_expression = BooleanExpression.parse

        condition = parse_expression(TokenStream(token.expression))

        block_token = stream.current()
        assert block_token is not None
        consequence = BlockNode(block_token, parse_block(stream, end=self.end_block))

        alternatives: list[ConditionalBlockNode] = []
        alternative: BlockNode | None = None

        while stream.is_tag("elsif"):
            alternative_token = next(stream)
            assert isinstance(alternative_token, Markup.Tag)

            alternative_expression = parse_expression(
                TokenStream(alternative_token.expression)
            )

            alternative_block = parse_block(stream, self.end_block)
            alternatives.append(
                ConditionalBlockNode(
                    alternative_token,
                    alternative_block,
                    alternative_expression,
                )
            )

        if stream.is_tag("else"):
            next(stream)
            alternative_token = stream.current()
            alternative_block = parse_block(stream, self.end_block)
            alternative = BlockNode(alternative_token, alternative_block)

        return self.node_class(
            token,
            condition,
            consequence,
            alternatives,
            alternative,
        )
