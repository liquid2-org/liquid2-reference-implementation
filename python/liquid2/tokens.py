"""A wrapper for token iterators that lets us step through and peek ahead."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Container
from typing import Type

from _liquid2 import Markup
from more_itertools import peekable

from .exceptions import LiquidSyntaxError

if TYPE_CHECKING:
    from _liquid2 import TokenT


class TokenStream(peekable):  # type: ignore
    """Step through or iterate a stream of tokens.

    Note that _peek()_ has been redefined to return self[1] rather than
    self[0]. Use _current_ to get self[0].

    """

    def __str__(self) -> str:  # pragma: no cover
        try:
            return f"current: {self.current()}, next: {self.peek()}"
        except StopIteration:
            return "EOI"

    def current(self) -> TokenT | None:
        """Return the next token in the stream or None if there are no tokens."""
        try:
            return self[0]  # type: ignore
        except IndexError:
            return None

    def peek(self) -> TokenT | None:  # type: ignore
        """Return the item at self[1]."""
        try:
            return self[1]  # type: ignore
        except IndexError:
            return None

    def push(self, token: TokenT) -> None:
        """Push a token back on to the stream."""
        self.prepend(token)

    def expect(self, typ: Type[TokenT]) -> None:
        """Raise a _LiquidSyntaxError_ if the current token type doesn't match _typ_."""
        token = self.current()
        if not isinstance(token, typ):
            raise LiquidSyntaxError(
                f"expected {typ.__name__}, found {token.__class__.__name__}",
                token=token,
            )

    def expect_peek(self, typ: Type[TokenT]) -> None:
        """Raise a _LiquidSyntaxError_ if the next token type does not match _typ_."""
        token = self.peek()
        if not isinstance(token, typ):
            raise LiquidSyntaxError(token=token)

    def is_tag(self, tag_name: str) -> bool:
        """Return _True_ if the current token is a tag named _tag_name_."""
        token = self.current()
        if isinstance(token, Markup.Tag):
            return token.name == tag_name
        return False

    def is_one_of(self, tag_names: Container[str]) -> bool:
        """Return _True_ if the current token is a tag with a name in _tag_names_."""
        token = self.current()
        if isinstance(token, Markup.Tag):
            return token.name in tag_names
        return False

    def peek_one_of(self, tag_names: Container[str]) -> bool:
        """Return _True_ if the next token is a tag with a name in _tag_names_."""
        peeked = self.peek()
        if isinstance(peeked, Markup.Tag):
            return peeked.name in tag_names
        return False
