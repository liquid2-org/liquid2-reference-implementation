"""JSONPath exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from liquid2 import TokenT


class JSONPathError(Exception):
    """Base exception for all errors.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The start and end index of the token that caused this error.
    """

    def __init__(self, *args: object, token: TokenT | None = None) -> None:
        super().__init__(*args)
        self.token: TokenT | None = token

    def __str__(self) -> str:
        msg = super().__str__()

        if not self.token:
            return msg

        # TODO: token or line/column
        return f"{msg}"


class JSONPathSyntaxError(JSONPathError):
    """An exception raised when a error occurs during JSONPath expression parsing.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The start and end index of the token that caused this error.
    """

    def __init__(self, *args: object, token: TokenT) -> None:
        super().__init__(*args)
        self.token = token


class JSONPathTypeError(JSONPathError):
    """An exception raised due to a type error.

    This should only occur at when evaluating filter expressions.
    """


class JSONPathIndexError(JSONPathError):
    """An exception raised when an array index is out of range.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The start and end index of the token that caused this error.
    """

    def __init__(self, *args: object, token: TokenT) -> None:
        super().__init__(*args)
        self.token = token


class JSONPathNameError(JSONPathError):
    """An exception raised when an unknown function extension is called.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The start and end index of the token that caused this error.
    """

    def __init__(self, *args: object, token: TokenT) -> None:
        super().__init__(*args)
        self.token = token


class JSONPathLexerError(JSONPathError):
    """An exception raised from inside the lexer.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The start and end index of the token that caused this error.
    """

    def __init__(self, *args: object, token: TokenT) -> None:
        super().__init__(*args)
        self.token = token


class JSONPathRecursionError(JSONPathError):
    """An exception raised when the maximum recursion depth is reached.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The start and end index of the token that caused this error.
    """

    def __init__(self, *args: object, token: TokenT) -> None:
        super().__init__(*args)
        self.token = token
