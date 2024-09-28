"""Liquid token parser."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Container
from typing import cast

from _liquid2 import Markup

from .builtin import Content
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
        content = cast(Content, tags["__CONTENT"])
        output = tags["__OUTPUT"]
        raw = tags["__RAW"]

        default_trim = self.env.trim
        left_trim = default_trim

        nodes: list[Node] = []
        stream = TokenStream(tokens)

        while True:
            match stream.current():
                case Markup.Content():
                    nodes.append(content.parse(stream, left_trim=left_trim))
                    left_trim = default_trim
                case Markup.Comment(_, wc):
                    left_trim = wc[-1]
                    nodes.append(comment.parse(stream))
                case Markup.Raw(_, wc):
                    left_trim = wc[-1]
                    nodes.append(raw.parse(stream))
                case Markup.Output(_, wc):
                    left_trim = wc[-1]
                    nodes.append(output.parse(stream))
                case Markup.Tag(_, wc, name):
                    left_trim = wc[-1]
                    try:
                        nodes.append(tags[name].parse(stream))
                    except KeyError as err:
                        raise LiquidSyntaxError(
                            f"unknown tag '{name}'", token=stream.current()
                        ) from err
                case Markup.EOI() | None:
                    break

            next(stream, None)

        return nodes

    def parse_block(self, stream: TokenStream, end: Container[str]) -> list[Node]:
        """Parse markup tokens from _stream_ until wee find a tag in _end_."""
        tags = self.tags
        comment = tags["__COMMENT"]
        content = cast(Content, tags["__CONTENT"])
        output = tags["__OUTPUT"]
        raw = tags["__RAW"]

        default_trim = self.env.trim
        left_trim = default_trim

        nodes: list[Node] = []

        while True:
            match stream.current():
                case Markup.Content():
                    nodes.append(content.parse(stream, left_trim=left_trim))
                    left_trim = default_trim
                case Markup.Comment(_, wc):
                    left_trim = wc[-1]
                    nodes.append(comment.parse(stream))
                case Markup.Raw(_, wc):
                    left_trim = wc[-1]
                    nodes.append(raw.parse(stream))
                case Markup.Output(_, wc):
                    left_trim = wc[-1]
                    nodes.append(output.parse(stream))
                case Markup.Tag(_, wc, name):
                    if name in end:
                        break

                    left_trim = wc[-1]
                    try:
                        nodes.append(tags[name].parse(stream))
                    except KeyError as err:
                        raise LiquidSyntaxError(
                            f"unknown tag {name}", token=stream.current()
                        ) from err
                case Markup.EOI() | None:
                    break

            next(stream, None)

        return nodes


def skip_block(stream: TokenStream, end: Container[str]) -> None:
    """Advance the stream until we find a tag with a name in _end_."""
    while not stream.is_one_of(end):
        next(stream)
