"""A wrapper for token iterators that lets us step through and peek ahead."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING
from typing import Deque
from typing import Iterator

from .exceptions import LiquidSyntaxError

if TYPE_CHECKING:
    from _liquid2 import Markup
    # from _liquid2 import Token


class TokenStream:
    """Step through or iterate a stream of tokens."""

    def __init__(self, tokens: list[Markup]):
        self.iter = iter(tokens)
        self._pushed: Deque[Markup] = deque()
        self.current = next(self.iter)

    class TokenStreamIterator:
        """An iterable token stream."""

        def __init__(self, stream: TokenStream):
            self.stream = stream

        def __iter__(self) -> Iterator[Markup]:
            return self

        def __next__(self) -> Markup:
            # TODO
            raise NotImplementedError(":(")

    def __iter__(self) -> Iterator[Markup]:
        return self.TokenStreamIterator(self)

    def __next__(self) -> Markup:
        # TODO
        raise NotImplementedError(":(")

    def __str__(self) -> str:  # pragma: no cover
        buf = [
            f"current: {self.current}",
            f"next: {self.peek}",
        ]
        return "\n".join(buf)

    def next_token(self) -> Markup:
        """Return the next token from the stream."""
        return next(self)

    def peek(self) -> Markup:
        """Look at the next token."""
        # TODO
        raise NotImplementedError(":(")

    def close(self) -> None:
        """Close the stream."""
        # TODO
        raise NotImplementedError(":(")

    def expect(self, typ: str) -> None:
        """Raise a `LiquidSyntaxError` if the current token type doesn't match `typ`."""
        # TODO
        raise NotImplementedError(":(")

    def expect_peek(self, typ: str) -> None:
        """Raise a `LiquidSyntaxError` if the next token type does not match `typ`."""
        # TODO
        raise NotImplementedError(":(")
