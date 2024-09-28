"""Expression for built in, standard tags."""

from __future__ import annotations

import sys
from decimal import Decimal
from typing import TYPE_CHECKING
from typing import Any
from typing import Collection
from typing import Generic
from typing import Type
from typing import TypeVar
from typing import cast

from _liquid2 import RangeArgument
from _liquid2 import Token
from _liquid2 import parse_query
from markupsafe import Markup

from liquid2.exceptions import LiquidSyntaxError
from liquid2.expression import Expression
from liquid2.limits import to_int
from liquid2.query import compile

if TYPE_CHECKING:
    from _liquid2 import TokenT

    from liquid2.context import RenderContext
    from liquid2.query import Query as _Query
    from liquid2.tokens import TokenStream


class Null(Expression):
    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return other is None or isinstance(other, Null)

    def __repr__(self) -> str:  # pragma: no cover
        return "NIL()"

    def __str__(self) -> str:  # pragma: no cover
        return ""

    def evaluate(self, _: RenderContext) -> None:
        return None

    def children(self) -> list[Expression]:
        return []


NULL = Null()


class Empty(Expression):
    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Empty):
            return True
        return isinstance(other, (list, dict, str)) and not other

    def __repr__(self) -> str:  # pragma: no cover
        return "Empty()"

    def __str__(self) -> str:  # pragma: no cover
        return "empty"

    def evaluate(self, _: RenderContext) -> Empty:
        return self

    def children(self) -> list[Expression]:
        return []


EMPTY = Empty()


class Blank(Expression):
    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str) and (not other or other.isspace()):
            return True
        if isinstance(other, (list, dict)) and not other:
            return True
        return isinstance(other, Blank)

    def __repr__(self) -> str:  # pragma: no cover
        return "Blank()"

    def __str__(self) -> str:  # pragma: no cover
        return "blank"

    def evaluate(self, _: RenderContext) -> Blank:
        return self

    def children(self) -> list[Expression]:
        return []


BLANK = Blank()


class Continue(Expression):
    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Continue)

    def __repr__(self) -> str:  # pragma: no cover
        return "Continue()"

    def __str__(self) -> str:  # pragma: no cover
        return "continue"

    def evaluate(self, _: RenderContext) -> int:
        return 0

    def children(self) -> list[Expression]:
        return []


CONTINUE = Continue()


T = TypeVar("T")


class Literal(Expression, Generic[T]):
    __slots__ = ("value",)

    def __init__(self, value: T):
        self.value = value

    def __str__(self) -> str:
        return repr(self.value)

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __hash__(self) -> int:
        return hash(self.value)

    def __sizeof__(self) -> int:
        return sys.getsizeof(self.value)

    def evaluate(self, _: RenderContext) -> object:
        return self.value

    def children(self) -> list[Expression]:
        return []


class Boolean(Literal[bool]):
    __slots__ = ()

    def __init__(self, value: bool):  # noqa: FBT001
        super().__init__(value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Boolean) and self.value == other.value

    def __repr__(self) -> str:  # pragma: no cover
        return f"Boolean(value={self.value})"


TRUE = Boolean(True)  # noqa: FBT003
FALSE = Boolean(False)  # noqa: FBT003


class StringLiteral(Literal[str]):
    __slots__ = ()

    def __init__(self, value: str):
        super().__init__(value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StringLiteral) and self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:  # pragma: no cover
        return f"StringLiteral(value='{self.value}')"

    def __sizeof__(self) -> int:
        return sys.getsizeof(self.value)

    def evaluate(self, context: RenderContext) -> str | Markup:
        if context.auto_escape:
            return Markup(self.value)
        return self.value


class IntegerLiteral(Literal[int]):
    __slots__ = ()

    def __init__(self, value: int):
        super().__init__(value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, IntegerLiteral) and self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:  # pragma: no cover
        return f"IntegerLiteral(value={self.value})"


class FloatLiteral(Literal[float]):
    __slots__ = ()

    def __init__(self, value: float):
        super().__init__(value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FloatLiteral) and self.value == other.value

    def __repr__(self) -> str:  # pragma: no cover
        return f"FloatLiteral(value={self.value})"


class RangeLiteral(Expression):
    __slots__ = ("start", "stop")

    def __init__(self, start: Expression, stop: Expression):
        self.start = start
        self.stop = stop

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, RangeLiteral)
            and self.start == other.start
            and self.stop == other.stop
        )

    def __str__(self) -> str:
        return f"({self.start}..{self.stop})"

    def __hash__(self) -> int:
        return hash((self.start, self.stop))

    def __sizeof__(self) -> int:
        return (
            super().__sizeof__() + sys.getsizeof(self.start) + sys.getsizeof(self.stop)
        )

    def _make_range(self, start: Any, stop: Any) -> range:
        try:
            start = to_int(start)
        except ValueError:
            start = 0

        try:
            stop = to_int(stop)
        except ValueError:
            stop = 0

        # Descending ranges don't work
        if start > stop:
            return range(0)

        return range(start, stop + 1)

    def evaluate(self, context: RenderContext) -> range:
        return self._make_range(
            self.start.evaluate(context), self.stop.evaluate(context)
        )

    async def evaluate_async(self, context: RenderContext) -> range:
        return self._make_range(
            await self.start.evaluate_async(context),
            await self.stop.evaluate_async(context),
        )

    def children(self) -> list[Expression]:
        return [self.start, self.stop]


class Query(Expression):
    __slots__ = ("path", "token")

    def __init__(self, token: TokenT, path: _Query) -> None:
        self.path = path
        self.token = token

    def __str__(self) -> str:
        return str(self.path)

    def __hash__(self) -> int:
        return hash(self.path)

    def __sizeof__(self) -> int:
        return super().__sizeof__() + sys.getsizeof(self.path)

    # TODO: as_tuple?

    def evaluate(self, context: RenderContext) -> object:
        return context.get(self.path, token=self.token)

    # TODO: async
    # TODO: children


Primitive = Literal[Any] | RangeLiteral | Query | Null


class FilteredExpression(Expression):
    __slots__ = ("left", "filters")

    def __init__(self, left: Expression, filters: list[Filter] | None = None) -> None:
        self.left = left
        self.filters = filters

    def evaluate(self, context: RenderContext) -> object:
        rv = self.left.evaluate(context)
        if self.filters:
            for f in self.filters:
                rv = f.evaluate(rv, context)
        return rv

    async def evaluate_async(self, context: RenderContext) -> object:
        rv = await self.left.evaluate_async(context)
        if self.filters:
            for f in self.filters:
                rv = await f.evaluate_async(rv, context)
        return rv

    @staticmethod
    def parse(stream: TokenStream) -> FilteredExpression | TernaryFilteredExpression:
        """Return a new FilteredExpression parsed from _tokens_."""
        left = parse_primitive(next(stream, None))
        filters = Filter.parse(stream, delim=(Token.Pipe,))

        if isinstance(stream.current(), Token.If):
            return TernaryFilteredExpression.parse(
                FilteredExpression(left, filters), stream
            )
        return FilteredExpression(left, filters)


def parse_primitive(token: TokenT | None) -> Expression:  # noqa: PLR0911
    """Parse _token_ as a primitive expression."""
    match token:
        case Token.True_():
            return TRUE
        case Token.False_():
            return FALSE
        case Token.Null():
            return NULL
        case Token.Word(_, value):
            if value == "empty":
                return EMPTY
            if value == "blank":
                return BLANK
            return Query(token, compile(parse_query(value)))
        case Token.RangeLiteral(_, start, stop):
            return RangeLiteral(parse_primitive(start), parse_primitive(stop))
        case Token.StringLiteral(_, value) | RangeArgument.StringLiteral(_, value):
            return StringLiteral(value)
        case Token.IntegerLiteral(_, value) | RangeArgument.IntegerLiteral(_, value):
            return IntegerLiteral(value)
        case Token.FloatLiteral(_, value) | RangeArgument.FloatLiteral(_, value):
            return FloatLiteral(value)
        case Token.Query(_, path) | RangeArgument.Query(_, path):
            return Query(token, compile(path))
        case _:
            raise LiquidSyntaxError(
                f"expected a primitive expression, found {token.__class__.__name__}",
                token=token,
            )


class TernaryFilteredExpression(Expression):
    __slots__ = ("left", "condition", "alternative", "filters", "tail_filters")

    def __init__(
        self,
        left: FilteredExpression,
        condition: BooleanExpression,
        alternative: Expression | None = None,
        filters: list[Filter] | None = None,
        tail_filters: list[Filter] | None = None,
    ) -> None:
        self.left = left
        self.condition = condition
        self.alternative = alternative
        self.filters = filters
        self.tail_filters = tail_filters

    def evaluate(self, context: RenderContext) -> object:
        rv: object = None

        if self.condition.evaluate(context):
            rv = self.left.evaluate(context)
        elif self.alternative:
            rv = self.alternative.evaluate(context)
            if self.filters:
                for f in self.filters:
                    rv = f.evaluate(rv, context)

        if self.tail_filters:
            for f in self.tail_filters:
                rv = f.evaluate(rv, context)

        return rv

    async def evaluate_async(self, context: RenderContext) -> object:
        rv: object = None

        if await self.condition.evaluate_async(context):
            rv = await self.left.evaluate_async(context)
        elif self.alternative:
            rv = await self.alternative.evaluate_async(context)
            if self.filters:
                for f in self.filters:
                    rv = await f.evaluate_async(rv, context)

        if self.tail_filters:
            for f in self.tail_filters:
                rv = await f.evaluate_async(rv, context)

        return rv

    @staticmethod
    def parse(
        expr: FilteredExpression, stream: TokenStream
    ) -> TernaryFilteredExpression:
        """Return a new TernaryFilteredExpression parsed from tokens in _stream_."""
        stream.expect(Token.If)
        next(stream)
        condition = BooleanExpression.parse(stream)
        alternative: Expression | None = None
        filters: list[Filter] | None = None
        tail_filters: list[Filter] | None = None

        if isinstance(stream.current(), Token.Else):
            next(stream)
            alternative = parse_primitive(next(stream, None))

            if isinstance(stream.current(), Token.Pipe):
                filters = Filter.parse(stream, delim=(Token.Pipe,))

        if isinstance(stream.current(), Token.DoublePipe):
            tail_filters = Filter.parse(stream, delim=(Token.Pipe, Token.DoublePipe))

        return TernaryFilteredExpression(
            expr, condition, alternative, filters, tail_filters
        )


class Filter:
    __slots__ = ("name", "args", "token")

    def __init__(
        self,
        token: TokenT,
        name: str,
        arguments: list[KeywordArgument | PositionalArgument],
    ) -> None:
        self.token = token
        self.name = name
        self.args = arguments

    def __str__(self) -> str:
        if self.args:
            return f"{self.name}: {''.join(str(arg for arg in self.args))}"
        return self.name

    def evaluate(self, left: object, context: RenderContext) -> object:
        func = context.filter(self.name, token=self.token)
        positional_args, keyword_args = self.evaluate_args(context)
        return func(left, *positional_args, **keyword_args)

    async def evaluate_async(self, left: object, context: RenderContext) -> object:
        func = context.filter(self.name, token=self.token)
        positional_args, keyword_args = await self.evaluate_args_async(context)

        if hasattr(func, "filter_async"):
            # TODO:
            raise NotImplementedError(":(")
        return func(left, *positional_args, **keyword_args)

    def evaluate_args(
        self, context: RenderContext
    ) -> tuple[list[object], dict[str, object]]:
        positional_args: list[object] = []
        keyword_args: dict[str, object] = {}
        for arg in self.args:
            name, value = arg.evaluate(context)
            if name:
                keyword_args[name] = value
            else:
                positional_args.append(value)

        return positional_args, keyword_args

    async def evaluate_args_async(
        self, context: RenderContext
    ) -> tuple[list[object], dict[str, object]]:
        positional_args: list[object] = []
        keyword_args: dict[str, object] = {}
        for arg in self.args:
            name, value = await arg.evaluate_async(context)
            if name:
                keyword_args[name] = value
            else:
                positional_args.append(value)

        return positional_args, keyword_args

    @staticmethod
    def parse(
        stream: TokenStream,
        *,
        delim: tuple[Type[Token.Pipe] | Type[Token.DoublePipe], ...],
    ) -> list[Filter]:
        """Parse as any filters as possible from tokens in _stream_."""
        filters: list[Filter] = []

        while isinstance(stream.current(), delim):
            next(stream)
            stream.expect(Token.Word)
            filter_token = cast(Token.Word, next(stream))
            filter_name = filter_token.value
            filter_arguments: list[KeywordArgument | PositionalArgument] = []

            if isinstance(stream.current(), Token.Colon):
                next(stream)  # Move past ':'
                while True:
                    token = stream.current()
                    match token:
                        case Token.Word(_, value):
                            if isinstance(
                                stream.current(), (Token.Assign, Token.Colon)
                            ):
                                # A named or keyword argument
                                next(stream)  # skip = or :
                                filter_arguments.append(
                                    KeywordArgument(
                                        value, parse_primitive(next(stream, None))
                                    )
                                )
                            else:
                                # A positional query that is a single word
                                filter_arguments.append(
                                    PositionalArgument(
                                        Query(token, compile(parse_query(value)))
                                    )
                                )
                        case Token.Query(_, path):
                            filter_arguments.append(
                                PositionalArgument(Query(token, compile(path)))
                            )
                        case (
                            Token.IntegerLiteral()
                            | Token.FloatLiteral()
                            | Token.StringLiteral()
                        ):
                            filter_arguments.append(
                                PositionalArgument(parse_primitive(next(stream)))
                            )
                        case Token.Comma():
                            # XXX: leading, trailing and duplicate commas are OK
                            next(stream, None)
                        case _:
                            break

                    next(stream, None)

            filters.append(Filter(filter_token, filter_name, filter_arguments))

        return filters


class KeywordArgument:
    __slots__ = ("name", "value")

    def __init__(self, name: str, value: Expression) -> None:
        self.name = name
        self.value = value

    def evaluate(self, context: RenderContext) -> tuple[str, object]:
        return (self.name, self.value.evaluate(context))

    async def evaluate_async(self, context: RenderContext) -> tuple[str, object]:
        return (self.name, await self.value.evaluate_async(context))


class PositionalArgument:
    __slots__ = ("value",)

    def __init__(self, value: Expression) -> None:
        self.value = value

    def evaluate(self, context: RenderContext) -> tuple[None, object]:
        return (None, self.value.evaluate(context))

    async def evaluate_async(self, context: RenderContext) -> tuple[None, object]:
        return (None, await self.value.evaluate_async(context))


class SymbolArgument:
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name


class BooleanExpression(Expression):
    __slots__ = ("expression",)

    def __init__(self, expression: Expression) -> None:
        self.expression = expression

    def evaluate(self, context: RenderContext) -> object:
        return is_truthy(self.expression.evaluate(context))

    async def evaluate_async(self, context: RenderContext) -> object:
        return is_truthy(await self.expression.evaluate_async(context))

    @staticmethod
    def parse(stream: TokenStream) -> BooleanExpression:
        """Return a new BooleanExpression parsed from tokens in _stream_."""
        return BooleanExpression(parse_boolean_primitive(stream))


PRECEDENCE_LOWEST = 1
PRECEDENCE_LOGICALRIGHT = 2
PRECEDENCE_LOGICAL_OR = 3
PRECEDENCE_LOGICAL_AND = 4
PRECEDENCE_RELATIONAL = 5
PRECEDENCE_MEMBERSHIP = 6
PRECEDENCE_PREFIX = 7

PRECEDENCES = {
    Token.Eq: PRECEDENCE_RELATIONAL,
    Token.Lt: PRECEDENCE_RELATIONAL,
    Token.Gt: PRECEDENCE_RELATIONAL,
    Token.Ne: PRECEDENCE_RELATIONAL,
    Token.Le: PRECEDENCE_RELATIONAL,
    Token.Ge: PRECEDENCE_RELATIONAL,
    Token.Contains: PRECEDENCE_MEMBERSHIP,
    Token.In: PRECEDENCE_MEMBERSHIP,
    Token.And: PRECEDENCE_LOGICAL_AND,
    Token.Or: PRECEDENCE_LOGICAL_OR,
    Token.Not: PRECEDENCE_PREFIX,
    Token.RightParen: PRECEDENCE_LOWEST,
}

BINARY_OPERATORS = frozenset(
    [
        Token.Eq,
        Token.Lt,
        Token.Gt,
        Token.Ne,
        Token.Le,
        Token.Ge,
        Token.Contains,
        Token.In,
        Token.And,
        Token.Or,
    ]
)


def parse_boolean_primitive(  # noqa: PLR0912
    stream: TokenStream, precedence: int = PRECEDENCE_LOWEST
) -> Expression:
    """Parse a Boolean expression from tokens in _stream_."""
    left: Expression
    token = next(stream, None)

    match token:
        case Token.True_():
            left = TRUE
        case Token.False_():
            left = FALSE
        case Token.Null():
            left = NULL
        case Token.Word(_, value):
            if value == "empty":
                left = EMPTY
            elif value == "blank":
                left = BLANK
            else:
                left = Query(token, compile(parse_query(value)))
        case Token.RangeLiteral(_, start, stop):
            left = RangeLiteral(parse_primitive(start), parse_primitive(stop))
        case Token.StringLiteral(_, value):
            left = StringLiteral(value)
        case Token.IntegerLiteral(_, value):
            left = IntegerLiteral(value)
        case Token.FloatLiteral(_, value):
            left = FloatLiteral(value)
        case Token.Query(_, path):
            left = Query(token, compile(path))
        case Token.Not():
            left = LogicalNotExpression.parse(stream)
        case Token.LeftParen():
            left = parse_grouped_expression(stream)
        case _:
            raise LiquidSyntaxError(
                "expected a primitive expression, "
                f"found {stream.current().__class__.__name__}",
                token=stream.current(),
            )

    while True:
        token = stream.current()
        if (
            not token
            or PRECEDENCES.get(token.__class__, PRECEDENCE_LOWEST) < precedence
        ):
            break

        if token.__class__ not in BINARY_OPERATORS:
            return left

        # next(stream)
        left = parse_infix_expression(stream, left)

    return left


def parse_infix_expression(stream: TokenStream, left: Expression) -> Expression:  # noqa: PLR0911
    """Return a logical, comparison, or membership expression parsed from _stream_."""
    token = next(stream, None)
    assert token is not None
    precedence = PRECEDENCES.get(token.__class__, PRECEDENCE_LOWEST)

    match token:
        case Token.Eq():
            return EqExpression(left, parse_boolean_primitive(stream, precedence))
        case Token.Lt():
            return LtExpression(left, parse_boolean_primitive(stream, precedence))
        case Token.Gt():
            return GtExpression(left, parse_boolean_primitive(stream, precedence))
        case Token.Ne():
            return NeExpression(left, parse_boolean_primitive(stream, precedence))
        case Token.Le():
            return LeExpression(left, parse_boolean_primitive(stream, precedence))
        case Token.Ge():
            return GeExpression(left, parse_boolean_primitive(stream, precedence))
        case Token.Contains():
            return ContainsExpression(left, parse_boolean_primitive(stream, precedence))
        case Token.In():
            return InExpression(left, parse_boolean_primitive(stream, precedence))
        case Token.And():
            return LogicalAndExpression(
                left, parse_boolean_primitive(stream, precedence)
            )
        case Token.Or():
            return LogicalOrExpression(
                left, parse_boolean_primitive(stream, precedence)
            )
        case _:
            raise LiquidSyntaxError(
                f"expected an infix expression, found {token.__class__.__name__}",
                token=token,
            )


def parse_grouped_expression(stream: TokenStream) -> Expression:
    """Parse an expression from tokens in _stream_ until the next right parenthesis."""
    expr = parse_boolean_primitive(stream)
    next(stream, None)  # XXX:

    while not isinstance(stream.current(), Token.RightParen):
        if stream.current() is None:
            raise LiquidSyntaxError("unbalanced parentheses", token=stream.current())

        if stream.current().__class__ not in BINARY_OPERATORS:
            raise LiquidSyntaxError(
                f"expected an infix expression, found {stream.current().__class__}",
                token=stream.current(),
            )

        expr = parse_infix_expression(stream, expr)

    stream.expect(Token.RightParen)
    return expr


class LogicalNotExpression(Expression):
    __slots__ = ("expression",)

    def __init__(self, expression: Expression) -> None:
        self.expression = expression

    def evaluate(self, context: RenderContext) -> object:
        return not is_truthy(self.expression.evaluate(context))

    async def evaluate_async(self, context: RenderContext) -> object:
        return not is_truthy(await self.expression.evaluate_async(context))

    @staticmethod
    def parse(stream: TokenStream) -> Expression:
        return LogicalNotExpression(parse_boolean_primitive(stream))


class LogicalAndExpression(Expression):
    __slots__ = ("left", "right")

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, context: RenderContext) -> object:
        return is_truthy(self.left.evaluate(context)) and is_truthy(
            self.right.evaluate(context)
        )

    async def evaluate_async(self, context: RenderContext) -> object:
        return is_truthy(await self.left.evaluate_async(context)) and is_truthy(
            await self.right.evaluate_async(context)
        )


class LogicalOrExpression(Expression):
    __slots__ = ("left", "right")

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, context: RenderContext) -> object:
        return is_truthy(self.left.evaluate(context)) or is_truthy(
            self.right.evaluate(context)
        )

    async def evaluate_async(self, context: RenderContext) -> object:
        return is_truthy(await self.left.evaluate_async(context)) or is_truthy(
            await self.right.evaluate_async(context)
        )


class EqExpression(Expression):
    __slots__ = ("left", "right")

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, context: RenderContext) -> object:
        return _eq(self.left.evaluate(context), self.right.evaluate(context))

    async def evaluate_async(self, context: RenderContext) -> object:
        return _eq(
            await self.left.evaluate_async(context),
            await self.right.evaluate_async(context),
        )


class NeExpression(Expression):
    __slots__ = ("left", "right")

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, context: RenderContext) -> object:
        return not _eq(self.left.evaluate(context), self.right.evaluate(context))

    async def evaluate_async(self, context: RenderContext) -> object:
        return not _eq(
            await self.left.evaluate_async(context),
            await self.right.evaluate_async(context),
        )


class LeExpression(Expression):
    __slots__ = ("left", "right")

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, context: RenderContext) -> object:
        left = self.left.evaluate(context)
        right = self.right.evaluate(context)
        return _eq(left, right) or _lt(left, right)

    async def evaluate_async(self, context: RenderContext) -> object:
        left = await self.left.evaluate_async(context)
        right = await self.right.evaluate_async(context)
        return _eq(left, right) or _lt(left, right)


class GeExpression(Expression):
    __slots__ = ("left", "right")

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, context: RenderContext) -> object:
        left = self.left.evaluate(context)
        right = self.right.evaluate(context)
        return _eq(left, right) or _lt(right, left)

    async def evaluate_async(self, context: RenderContext) -> object:
        left = await self.left.evaluate_async(context)
        right = await self.right.evaluate_async(context)
        return _eq(left, right) or _lt(right, left)


class LtExpression(Expression):
    __slots__ = ("left", "right")

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, context: RenderContext) -> object:
        # TODO: type error?
        return _lt(self.left.evaluate(context), self.right.evaluate(context))

    async def evaluate_async(self, context: RenderContext) -> object:
        return not _eq(
            await self.left.evaluate_async(context),
            await self.right.evaluate_async(context),
        )


class GtExpression(Expression):
    __slots__ = ("left", "right")

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, context: RenderContext) -> object:
        # TODO: type error?
        return _lt(self.right.evaluate(context), self.left.evaluate(context))

    async def evaluate_async(self, context: RenderContext) -> object:
        return _lt(
            await self.right.evaluate_async(context),
            await self.left.evaluate_async(context),
        )


class ContainsExpression(Expression):
    __slots__ = ("left", "right")

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, context: RenderContext) -> object:
        # TODO: type error?
        return _contains(self.left.evaluate(context), self.right.evaluate(context))

    async def evaluate_async(self, context: RenderContext) -> object:
        return _contains(
            await self.left.evaluate_async(context),
            await self.right.evaluate_async(context),
        )


class InExpression(Expression):
    __slots__ = ("left", "right")

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, context: RenderContext) -> object:
        # TODO: type error?
        return _contains(self.right.evaluate(context), self.left.evaluate(context))

    async def evaluate_async(self, context: RenderContext) -> object:
        return _contains(
            await self.right.evaluate_async(context),
            await self.left.evaluate_async(context),
        )


def is_truthy(obj: object) -> bool:
    """Return _True_ if _obj_ is considered Liquid truthy."""
    if hasattr(obj, "__liquid__"):
        obj = obj.__liquid__()
    return not (obj is False or obj is None)


def _eq(left: object, right: object) -> bool:
    if isinstance(right, (Empty, Blank)):
        left, right = right, left

    # Remember 1 == True and 0 == False in Python
    if isinstance(right, bool):
        left, right = right, left

    if isinstance(left, bool):
        return isinstance(right, bool) and left == right

    return left == right


def _lt(left: object, right: object) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return left < right

    if isinstance(left, bool) or isinstance(right, bool):
        return False

    if isinstance(left, (int, float, Decimal)) and isinstance(
        right, (int, float, Decimal)
    ):
        return left < right

    raise TypeError


def _contains(left: object, right: object) -> bool:
    if isinstance(left, str):
        return str(right) in left
    if isinstance(left, Collection):
        return right in left
    return False
