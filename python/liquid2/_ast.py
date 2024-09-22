"""Template abstract syntax tree."""

from __future__ import annotations

import sys
from abc import ABC
from abc import abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING
from typing import Any
from typing import Generic
from typing import TextIO
from typing import TypeVar

from markupsafe import Markup

from liquid2 import BooleanExpression as IRBooleanExpression
from liquid2 import BooleanOperator
from liquid2 import CommonArgument
from liquid2 import CompareOperator
from liquid2 import Node as ParseTreeNode
from liquid2 import Primitive as IRPrimitive
from liquid2.context import RenderContext

from .limits import to_int
from .query import compile
from .query import from_symbol
from .stringify import to_liquid_string

if TYPE_CHECKING:
    from liquid2 import FilteredExpression as IRFilteredExpression
    from liquid2 import InlineCondition as IRInlineCondition
    from liquid2 import Template as ParseTree

    from .context import RenderContext
    from .environment import Environment
    from .query import Query as _Query


class AST:
    """Template abstract syntax tree."""

    def __init__(self, env: Environment, parse_tree: ParseTree) -> None:
        self.env = env
        self.nodes = self._make(parse_tree)

    def _make(self, parse_tree: ParseTree) -> list[_Node]:
        return [self._make_node(node) for node in parse_tree.liquid]

    def _make_node(self, node: ParseTreeNode) -> _Node:
        match node:
            case ParseTreeNode.Content():
                return _ContentNode(node)
            case ParseTreeNode.Output():
                return _OutputNode(node)
            # TODO:
        return _TodoNode()


class _Node(ABC):
    __slots__ = ()

    def render(self, context: RenderContext, buffer: TextIO) -> int:
        return self.render_to_output(context, buffer)

    @abstractmethod
    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        """Render the node to the output buffer.

        Return:
            The number of "characters" written to the output buffer.
        """

    async def render_to_output_async(
        self, context: RenderContext, buffer: TextIO
    ) -> int:
        """An async version of _render_to_output_."""
        return self.render_to_output(context, buffer)


class _TodoNode(_Node):
    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        raise NotImplementedError(":(")


class _ContentNode(_Node):
    __slots__ = ("text",)

    def __init__(self, node: ParseTreeNode.Content) -> None:
        super().__init__()
        self.text = node.text

    def render_to_output(self, _context: RenderContext, buffer: TextIO) -> int:
        buffer.write(self.text)
        return len(self.text)


class _OutputNode(_Node):
    __slots__ = ("wc", "expression")

    def __init__(self, node: ParseTreeNode.Output) -> None:
        super().__init__()
        self.wc = node.wc
        self.expression: Expression = FilteredExpression(node.expression)
        if node.expression.condition:
            self.expression = TernaryFilteredExpression(
                self.expression, node.expression.condition
            )

    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        return buffer.write(
            to_liquid_string(self.expression.evaluate(context), context.auto_escape)
        )

    async def render_to_output_async(
        self, context: RenderContext, buffer: TextIO
    ) -> int:
        return buffer.write(
            to_liquid_string(
                await self.expression.evaluate_async(context), context.auto_escape
            )
        )


class Expression(ABC):
    __slots__ = ()

    @abstractmethod
    def evaluate(self, context: RenderContext) -> object:
        """Evaluate the expression in the given render context."""

    async def evaluate_async(self, context: RenderContext) -> object:
        """An async version of `liquid.expression.Expression.evaluate`."""
        return self.evaluate(context)

    def children(self) -> list[Expression]:
        """Return a list of child expressions."""
        raise NotImplementedError(f"{self.__class__.__name__}.children")


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

    def __repr__(self) -> str:  # pragma: no cover
        return f"RangeLiteral(start={self.start}, stop={self.stop})"

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
    __slots__ = ("path",)

    def __init__(self, path: _Query) -> None:
        self.path = path

    def __str__(self) -> str:
        return str(self.path)

    def __hash__(self) -> int:
        return hash(self.path)

    def __sizeof__(self) -> int:
        return super().__sizeof__() + sys.getsizeof(self.path)

    # TODO: as_tuple?

    def evaluate(self, context: RenderContext) -> object:
        return context.get(self.path)

    # TODO: async
    # TODO: children


Primitive = Literal[Any] | RangeLiteral | Query | Null


def _primitive(v: IRPrimitive) -> Primitive:  # noqa: PLR0911
    match v:
        case IRPrimitive.TrueLiteral():
            return TRUE
        case IRPrimitive.FalseLiteral():
            return FALSE
        case IRPrimitive.NullLiteral():
            return NULL
        case IRPrimitive.Integer(value):
            return IntegerLiteral(value)
        case IRPrimitive.Float(value):
            return FloatLiteral(value)
        case IRPrimitive.StringLiteral(value):
            return StringLiteral(value)
        case IRPrimitive.Range(start, stop):
            return RangeLiteral(IntegerLiteral(start), IntegerLiteral(stop))
        case IRPrimitive.Query(path):
            return Query(compile(path))
        case _:
            raise NotImplementedError(":(")


def _argument(arg: CommonArgument) -> KeywordArgument | PositionalArgument:
    match arg:
        case CommonArgument.Keyword(name, value):
            return KeywordArgument(name, _primitive(value))
        case CommonArgument.Positional(value):
            return PositionalArgument(_primitive(value))
        case CommonArgument.Symbol(name):
            return PositionalArgument(_symbol_as_query(name))
        case _:
            raise NotImplementedError("(")


def _symbol_as_query(s: str) -> Query:
    return Query(from_symbol(s))


class FilteredExpression(Expression):
    __slots__ = ("left", "filters")

    def __init__(self, expr: IRFilteredExpression) -> None:
        self.left = _primitive(expr.left)
        self.filters: list[Filter] = []

        if expr.filters:
            for f in expr.filters:
                if f.args:
                    args = [_argument(arg) for arg in f.args]
                else:
                    args = []
                self.filters.append(Filter(f.name, args))

    def evaluate(self, context: RenderContext) -> object:
        rv = self.left.evaluate(context)
        for f in self.filters:
            rv = f.evaluate(rv, context)
        return rv

    async def evaluate_async(self, context: RenderContext) -> object:
        rv = await self.left.evaluate_async(context)
        for f in self.filters:
            rv = await f.evaluate_async(rv, context)
        return rv


class TernaryFilteredExpression(Expression):
    __slots__ = ("left", "condition", "alternative", "filters", "tail_filters")

    def __init__(
        self,
        left: FilteredExpression,
        expr: IRInlineCondition,
    ) -> None:
        self.left = left
        self.condition = BooleanExpression(_expr(expr.expr))
        self.alternative = _primitive(expr.alternative) if expr.alternative else None
        self.filters: list[Filter] = []
        self.tail_filters: list[Filter] = []

        if expr.alternative_filters:
            for f in expr.alternative_filters:
                if f.args:
                    args = [_argument(arg) for arg in f.args]
                else:
                    args = []
                self.filters.append(Filter(f.name, args))

        if expr.tail_filters:
            for f in expr.tail_filters:
                if f.args:
                    args = [_argument(arg) for arg in f.args]
                else:
                    args = []
                self.tail_filters.append(Filter(f.name, args))

    def evaluate(self, context: RenderContext) -> object:
        rv: object = None

        if self.condition.evaluate(context):
            rv = self.left.evaluate(context)
        elif self.alternative:
            rv = self.alternative.evaluate(context)
            for f in self.filters:
                f.evaluate(rv, context)

        if self.tail_filters:
            for f in self.tail_filters:
                f.evaluate(rv, context)

        return rv

    async def evaluate_async(self, context: RenderContext) -> object:
        rv: object = None

        if await self.condition.evaluate_async(context):
            rv = await self.left.evaluate_async(context)
        elif self.alternative:
            rv = await self.alternative.evaluate_async(context)
            for f in self.filters:
                await f.evaluate_async(rv, context)

        if self.tail_filters:
            for f in self.tail_filters:
                await f.evaluate_async(rv, context)

        return rv


class Filter:
    __slots__ = ("name", "args")

    def __init__(
        self, name: str, arguments: list[KeywordArgument | PositionalArgument]
    ) -> None:
        self.name = name
        self.args = arguments

    def __str__(self) -> str:
        if self.args:
            return f"{self.name}: {''.join(str(arg for arg in self.args))}"
        return self.name

    def evaluate(self, left: object, context: RenderContext) -> object:
        func = context.filter(self.name)
        positional_args, keyword_args = self.evaluate_args(context)
        return func(left, *positional_args, **keyword_args)

    async def evaluate_async(self, left: object, context: RenderContext) -> object:
        func = context.filter(self.name)
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


def _expr(expression: IRBooleanExpression) -> Expression:  # noqa: PLR0911
    match expression:
        case IRBooleanExpression.Primitive(expr):
            return _primitive(expr)
        case IRBooleanExpression.LogicalNot(expr):
            return LogicalNotExpression(_expr(expr))
        case IRBooleanExpression.Logical(left, BooleanOperator.And, right):
            return LogicalAndExpression(_expr(left), _expr(right))
        case IRBooleanExpression.Logical(left, BooleanOperator.Or, right):
            return LogicalOrExpression(_expr(left), _expr(right))
        case IRBooleanExpression.Comparison(left, CompareOperator.Eq, right):
            return EqExpression(_expr(left), _expr(right))
        case IRBooleanExpression.Comparison(left, CompareOperator.Ne, right):
            return NeExpression(_expr(left), _expr(right))
        case IRBooleanExpression.Comparison(left, CompareOperator.Le, right):
            return LeExpression(_expr(left), _expr(right))
        case IRBooleanExpression.Comparison(left, CompareOperator.Ge, right):
            return GeExpression(_expr(left), _expr(right))
        case IRBooleanExpression.Comparison(left, CompareOperator.Lt, right):
            return LtExpression(_expr(left), _expr(right))
        case IRBooleanExpression.Comparison(left, CompareOperator.Gt, right):
            return GtExpression(_expr(left), _expr(right))
        case IRBooleanExpression.Membership(left, op, right):
            raise NotImplementedError(":(")
        case _:
            raise NotImplementedError(":(")


class BooleanExpression(Expression):
    __slots__ = ("expression",)

    def __init__(self, expression: Expression) -> None:
        self.expression = expression

    def evaluate(self, context: RenderContext) -> object:
        return is_truthy(self.expression.evaluate(context))

    async def evaluate_async(self, context: RenderContext) -> object:
        return is_truthy(await self.expression.evaluate_async(context))


class LogicalNotExpression(Expression):
    __slots__ = ("expression",)

    def __init__(self, expression: Expression) -> None:
        self.expression = expression

    def evaluate(self, context: RenderContext) -> object:
        return not is_truthy(self.expression.evaluate(context))

    async def evaluate_async(self, context: RenderContext) -> object:
        return not is_truthy(await self.expression.evaluate_async(context))


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
        return _eq(self.left.evaluate(context), is_truthy(self.right.evaluate(context)))

    async def evaluate_async(self, context: RenderContext) -> object:
        return _eq(
            await self.left.evaluate_async(context),
            is_truthy(await self.right.evaluate_async(context)),
        )


class NeExpression(Expression):
    __slots__ = ("left", "right")

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, context: RenderContext) -> object:
        return not _eq(
            self.left.evaluate(context), is_truthy(self.right.evaluate(context))
        )

    async def evaluate_async(self, context: RenderContext) -> object:
        return not _eq(
            await self.left.evaluate_async(context),
            is_truthy(await self.right.evaluate_async(context)),
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
        return _lt(self.left.evaluate(context), is_truthy(self.right.evaluate(context)))

    async def evaluate_async(self, context: RenderContext) -> object:
        return not _eq(
            await self.left.evaluate_async(context),
            is_truthy(await self.right.evaluate_async(context)),
        )


class GtExpression(Expression):
    __slots__ = ("left", "right")

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, context: RenderContext) -> object:
        # TODO: type error?
        return _lt(self.right.evaluate(context), is_truthy(self.left.evaluate(context)))

    async def evaluate_async(self, context: RenderContext) -> object:
        return _lt(
            await self.right.evaluate_async(context),
            is_truthy(await self.left.evaluate_async(context)),
        )


def is_truthy(obj: object) -> bool:
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
