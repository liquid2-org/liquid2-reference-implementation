"""A wrapper for token iterators that lets us step through and peek ahead."""

from __future__ import annotations

from typing import Type

from _liquid2 import TokenT
from more_itertools import peekable

from .exceptions import LiquidSyntaxError


class TokenStream(peekable[TokenT]):
    """Step through or iterate a stream of tokens."""

    def __str__(self) -> str:  # pragma: no cover
        try:
            return f"current: {self[0]}, next: {self.peek(default=None)}"
        except StopIteration:
            return "EOI"

    @property
    def current(self) -> TokenT | None:
        """Return the current token in the stream or None if there are no tokens."""
        try:
            return self[0]
        except StopIteration:
            return None

    def push(self, token: TokenT) -> None:
        """Push a token back on to the stream."""
        self.prepend(token)

    def expect(self, typ: Type[TokenT]) -> None:
        """Raise a _LiquidSyntaxError_ if the current token type doesn't match _typ_."""
        if not isinstance(self.current, typ):
            raise LiquidSyntaxError(token=self.current)

    def expect_peek(self, typ: Type[TokenT]) -> None:
        """Raise a _LiquidSyntaxError_ if the next token type does not match _typ_."""
        token = self.peek(default=None)
        if not isinstance(token, typ):
            raise LiquidSyntaxError(token=token)
