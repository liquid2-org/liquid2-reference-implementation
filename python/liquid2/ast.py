"""Base class for all template nodes."""

from abc import ABC
from abc import abstractmethod
from typing import TextIO

from .context import RenderContext


class Node(ABC):
    """Base class for all template nodes."""

    __slots__ = ()

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
