"""Liquid token parser."""

from __future__ import annotations

from typing import TYPE_CHECKING

from _liquid2 import Markup

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
        stream = TokenStream(tokens)
        raise NotImplementedError(":(")
