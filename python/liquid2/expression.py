"""Base class for all Liquid expressions."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import RenderContext


class Expression(ABC):
    """Base class for all Liquid expressions."""

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
