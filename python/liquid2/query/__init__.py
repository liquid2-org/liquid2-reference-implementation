from .environment import _JSONPathEnvironment
from .query import JSONPathQuery as Query  # noqa: D104

__all__ = [
    "compile",
    "from_symbol",
    "Query",
]


DEFAULT_ENV = _JSONPathEnvironment()
compile = DEFAULT_ENV.compile  # noqa: A001
from_symbol = DEFAULT_ENV.from_symbol
