"""Base class for all template nodes."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import TextIO

if TYPE_CHECKING:
    from _liquid2 import TokenT

    from .context import RenderContext


class Node(ABC):
    """Base class for all template nodes."""

    __slots__ = ("token",)

    def __init__(self, token: TokenT) -> None:
        super().__init__()
        self.token = token

    def render(self, context: RenderContext, buffer: TextIO) -> int:
        """Write this node's content to _buffer_."""
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
