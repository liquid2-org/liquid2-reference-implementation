from __future__ import annotations

from enum import Enum

class Whitespace(Enum):
    Plus = ...
    Minus = ...
    Smart = ...
    Default = ...

class WhitespaceControl:
    @property
    def left(self) -> Whitespace: ...
    @property
    def right(self) -> Whitespace: ...

class Node:
    class Content:
        __match_args__ = ("text",)
        @property
        def text(self) -> str: ...

    class Output:
        @property
        def wc(self) -> WhitespaceControl: ...
        @property
        def expression(self) -> FilteredExpression: ...

    class Raw:
        @property
        def wc(self) -> tuple[WhitespaceControl, WhitespaceControl]: ...
        @property
        def text(self) -> str: ...

    class Comment:
        @property
        def wc(self) -> WhitespaceControl: ...
        @property
        def text(self) -> str: ...
        @property
        def hashes(self) -> str: ...

    class AssignTag:
        @property
        def wc(self) -> WhitespaceControl: ...
        @property
        def identifier(self) -> str: ...
        @property
        def expression(self) -> FilteredExpression: ...

    class CaptureTag:
        @property
        def wc(self) -> tuple[WhitespaceControl, WhitespaceControl]: ...
        @property
        def identifier(self) -> str: ...
        @property
        def block(self) -> list[Node]: ...

    class CaseTag:
        @property
        def wc(self) -> tuple[WhitespaceControl, WhitespaceControl]: ...
        @property
        def arg(self) -> Primitive: ...
        @property
        def whens(self) -> list[WhenTag]: ...
        @property
        def default(self) -> list[ElseTag]: ...

    class CycleTag:
        @property
        def wc(self) -> WhitespaceControl: ...
        @property
        def name(self) -> None | str: ...
        @property
        def args(self) -> list[Primitive]: ...

    class DecrementTag:
        @property
        def wc(self) -> WhitespaceControl: ...
        @property
        def name(self) -> str: ...

    class IncrementTag:
        @property
        def wc(self) -> WhitespaceControl: ...
        @property
        def name(self) -> str: ...

    class EchoTag:
        @property
        def wc(self) -> WhitespaceControl: ...
        @property
        def expression(self) -> FilteredExpression: ...

    class ForTag:
        @property
        def wc(self) -> tuple[WhitespaceControl, WhitespaceControl]: ...
        @property
        def name(self) -> str: ...
        @property
        def iterable(self) -> Primitive: ...
        @property
        def limit(self) -> None | Primitive: ...
        @property
        def offset(self) -> None | Primitive: ...
        @property
        def reversed(self) -> bool: ...
        @property
        def block(self) -> list[Node]: ...
        @property
        def default(self) -> None | ElseTag: ...

    class BreakTag:
        @property
        def wc(self) -> WhitespaceControl: ...

    class ContinueTag:
        @property
        def wc(self) -> WhitespaceControl: ...

    class IfTag:
        @property
        def wc(self) -> tuple[WhitespaceControl, WhitespaceControl]: ...
        @property
        def condition(self) -> BooleanExpression: ...
        @property
        def block(self) -> list[Node]: ...
        @property
        def alternatives(self) -> list[ElsifTag]: ...
        @property
        def default(self) -> None | ElseTag: ...

    class UnlessTag:
        @property
        def wc(self) -> tuple[WhitespaceControl, WhitespaceControl]: ...
        @property
        def condition(self) -> BooleanExpression: ...
        @property
        def block(self) -> list[Node]: ...
        @property
        def alternatives(self) -> list[ElsifTag]: ...
        @property
        def default(self) -> None | ElseTag: ...

    class IncludeTag:
        @property
        def wc(self) -> WhitespaceControl: ...
        @property
        def target(self) -> Primitive: ...
        @property
        def repeat(self) -> bool: ...
        @property
        def variable(self) -> None | Primitive: ...
        @property
        def alias(self) -> None | str: ...
        @property
        def args(self) -> None | list[CommonArgument]: ...

    class RenderTag:
        @property
        def wc(self) -> WhitespaceControl: ...
        @property
        def target(self) -> Primitive: ...
        @property
        def repeat(self) -> bool: ...
        @property
        def variable(self) -> None | Primitive: ...
        @property
        def alias(self) -> None | str: ...
        @property
        def args(self) -> None | list[CommonArgument]: ...

    class LiquidTag:
        @property
        def wc(self) -> WhitespaceControl: ...
        @property
        def block(self) -> list[Node]: ...

    class TagExtension:
        @property
        def wc(self) -> tuple[WhitespaceControl, None | WhitespaceControl]: ...
        @property
        def name(self) -> str: ...
        @property
        def args(self) -> list[CommonArgument]: ...
        @property
        def block(self) -> None | list[Node]: ...
        @property
        def tags(self) -> None | list[Node]: ...

class FilteredExpression:
    @property
    def left(self) -> Primitive: ...
    @property
    def filters(self) -> None | list[Filter]: ...
    @property
    def condition(self) -> None | InlineCondition: ...

class Filter:
    @property
    def name(self) -> str: ...
    @property
    def args(self) -> None | list[CommonArgument]: ...

class CommonArgument:
    @property
    def value(self) -> None | Primitive: ...
    @property
    def name(self) -> None | str: ...

class InlineCondition:
    @property
    def expr(self) -> BooleanExpression: ...
    @property
    def alternative(self) -> None | Primitive: ...
    @property
    def alternative_filters(self) -> None | list[Filter]: ...
    @property
    def tail_filters(self) -> None | list[Filter]: ...

class BooleanExpression:
    class Primitive:
        __match_args__ = ("expr",)
        @property
        def expr(self) -> Primitive: ...

    class LogicalNot:
        __match_args__ = ("expr",)
        @property
        def expr(self) -> BooleanExpression: ...

    class Logical:
        __match_args__ = ("left", "operator", "right")
        @property
        def left(self) -> BooleanExpression: ...
        @property
        def operator(self) -> BooleanOperator: ...
        @property
        def right(self) -> BooleanExpression: ...

    class Comparison:
        __match_args__ = ("left", "operator", "right")
        @property
        def left(self) -> BooleanExpression: ...
        @property
        def operator(self) -> ComparisonOperator: ...
        @property
        def right(self) -> BooleanExpression: ...

    class Membership:
        __match_args__ = ("left", "operator", "right")
        @property
        def left(self) -> BooleanExpression: ...
        @property
        def operator(self) -> MembershipOperator: ...
        @property
        def right(self) -> BooleanExpression: ...

class ElseTag:
    @property
    def wc(self) -> WhitespaceControl: ...
    @property
    def block(self) -> list[Node]: ...

class ElsifTag:
    @property
    def wc(self) -> WhitespaceControl: ...
    @property
    def condition(self) -> BooleanExpression: ...
    @property
    def block(self) -> list[Node]: ...

class WhenTag:
    @property
    def wc(self) -> WhitespaceControl: ...
    @property
    def args(self) -> list[Primitive]: ...
    @property
    def block(self) -> list[Node]: ...

class BooleanOperator(Enum):
    And = ...
    Or = ...

class ComparisonOperator(Enum):
    Eq = ...
    Ne = ...
    Ge = ...
    Gt = ...
    Le = ...
    Lt = ...

class MembershipOperator(Enum):
    In = ...
    NotIn = ...
    Contains = ...
    NotContains = ...

class Primitive:
    class TrueLiteral: ...
    class FalseLiteral: ...
    class NullLiteral: ...

    class Integer:
        __match_args__ = "value"
        @property
        def value(self) -> int: ...

    class Float:
        __match_args__ = "value"
        @property
        def value(self) -> float: ...

    class StringLiteral:
        __match_args__ = "value"
        @property
        def value(self) -> str: ...

    class Range:
        __match_args__ = ("start", "stop")
        @property
        def start(self) -> int: ...
        @property
        def stop(self) -> int: ...

    class Query:
        __match_args__ = "path"
        @property
        def path(self) -> Query: ...

class Template:
    @property
    def liquid(self) -> list[Node]: ...

class ComparisonOp(Enum):
    Eq = ...
    Ne = ...
    Ge = ...
    Gt = ...
    Le = ...
    Lt = ...

class LogicalOp(Enum):
    And = ...
    Or = ...

class FilterExpression:
    class True_: ...
    class False_: ...
    class Null: ...

    class String:
        __match_args__ = ("value",)
        @property
        def value(self) -> str: ...

    class Int:
        __match_args__ = ("value",)
        @property
        def value(self) -> int: ...

    class Float:
        __match_args__ = ("value",)
        @property
        def value(self) -> float: ...

    class Not:
        __match_args__ = ("expression",)
        @property
        def expression(self) -> FilterExpression: ...

    class Logical:
        __match_args__ = ("left", "operator", "right")
        @property
        def left(self) -> FilterExpression: ...
        @property
        def operator(self) -> LogicalOp: ...
        @property
        def right(self) -> FilterExpression: ...

    class Comparison:
        __match_args__ = ("left", "operator", "right")
        @property
        def left(self) -> FilterExpression: ...
        @property
        def operator(self) -> ComparisonOp: ...
        @property
        def right(self) -> FilterExpression: ...

    class RelativeQuery:
        @property
        def query(self) -> Query: ...

    class RootQuery:
        @property
        def query(self) -> Query: ...

    class Function:
        @property
        def name(self) -> str: ...
        @property
        def args(self) -> list[FilterExpression]: ...

class Seleftor:
    class Name:
        __match_args__ = ("name",)
        @property
        def name(self) -> str: ...

    class Index:
        __match_args__ = ("index",)
        @property
        def index(self) -> int: ...

    class Slice:
        __match_args__ = ("start", "stop", "step")
        @property
        def start(self) -> int | None: ...
        @property
        def stop(self) -> int | None: ...
        @property
        def step(self) -> int | None: ...

    class Wild: ...

    class Filter:
        __match_args__ = ("expression",)
        @property
        def expression(self) -> FilterExpression: ...

SeleftorList = list[Seleftor]

class Segment:
    class Child:
        __match_args__ = ("seleftors", "span")
        @property
        def seleftors(self) -> SeleftorList: ...

    class Recursive:
        __match_args__ = ("seleftors", "span")
        @property
        def seleftors(self) -> SeleftorList: ...

class Query:
    @property
    def segments(self) -> list[Segment]: ...

def parse(source: str) -> Template: ...
