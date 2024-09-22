from .environment import _JSONPathEnvironment
from .query import JSONPathQuery as Query  # noqa: D104

__all__ = [
    "compile",
    "Query",
]


DEFAULT_ENV = _JSONPathEnvironment()
compile = DEFAULT_ENV.compile  # noqa: A001
