"""Liquid token parser."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Container

from _liquid2 import Markup

from .exceptions import LiquidSyntaxError
from .tokens import TokenStream

if TYPE_CHECKING:
    from .ast import Node
    from .environment import Environment


class Parser:
    """Liquid token parser."""

    def __init__(self, env: Environment) -> None:
        self.env = env
        self.tags = env.tags

    def parse(self, tokens: list[Markup]) -> list[Node]:
        """Parse _tokens_ into an abstract syntax tree."""
        tags = self.tags
        comment = tags["__COMMENT"]
        content = tags["__CONTENT"]
        output = tags["__OUTPUT"]
        raw = tags["__RAW"]

        nodes: list[Node] = []
        stream = TokenStream(tokens)

        while True:
            match next(stream, None):
                case Markup.Content():
                    nodes.append(content.parse(stream))
                case Markup.Comment():
                    nodes.append(comment.parse(stream))
                case Markup.Raw():
                    nodes.append(raw.parse(stream))
                case Markup.Output():
                    nodes.append(output.parse(stream))
                case Markup.Tag(name):
                    try:
                        nodes.append(tags[name].parse(stream))
                    except KeyError as err:
                        raise LiquidSyntaxError(
                            f"unknown tag {name}", token=stream.current
                        ) from err
                case Markup.EOI() | None:
                    break

        return nodes

    def parse_block(self, stream: TokenStream, end: Container[str]) -> list[Node]:
        """Parse markup tokens from _stream_ until wee find a tag in _end_."""
        tags = self.tags
        comment = tags["__COMMENT"]
        content = tags["__CONTENT"]
        output = tags["__OUTPUT"]
        raw = tags["__RAW"]

        nodes: list[Node] = []

        while not stream.is_one_of(end):
            match stream.current:
                case Markup.Content():
                    nodes.append(content.parse(stream))
                case Markup.Comment():
                    nodes.append(comment.parse(stream))
                case Markup.Raw():
                    nodes.append(raw.parse(stream))
                case Markup.Output():
                    nodes.append(output.parse(stream))
                case Markup.Tag(name):
                    try:
                        nodes.append(tags[name].parse(stream))
                    except KeyError as err:
                        raise LiquidSyntaxError(
                            f"unknown tag {name}", token=stream.current
                        ) from err
                case Markup.EOI() | None:
                    break

        return nodes


def skip_block(stream: TokenStream, end: Container[str]) -> None:
    """Advance the stream until we find a tag with a name in _end_."""
    while not stream.is_one_of(end):
        next(stream)
