from _liquid2 import parse_query

from .environment import JSONValue
from .environment import _JSONPathEnvironment
from .node import JSONPathNode
from .node import JSONPathNodeList
from .query import JSONPathQuery as Query

__all__ = [
    "compile",
    "from_symbol",
    "Query",
    "JSONPathNode",
    "JSONPathNodeList",
    "JSONValue",
]


DEFAULT_ENV = _JSONPathEnvironment()
compile = DEFAULT_ENV.compile  # noqa: A001
from_symbol = DEFAULT_ENV.from_symbol


def find(query: str, value: JSONValue) -> JSONPathNodeList:
    return compile(parse_query(query)).find(value)
