"""A parsed template, ready to be rendered."""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING
from typing import Any
from typing import Mapping
from typing import TextIO

from .context import RenderContext

if TYPE_CHECKING:
    from pathlib import Path

    from ._ast import _AST
    from .environment import Environment


class Template:
    """A parsed template ready to be rendered."""

    __slots__ = (
        "env",
        "ast",
        "name",
        "path",
        "global_data",
        "overlay_data",
    )

    def __init__(
        self,
        env: Environment,
        ast: _AST,
        *,
        name: str = "<string>",
        path: str | Path | None = None,
        global_data: Mapping[str, object] | None = None,
        overlay_data: Mapping[str, object] | None = None,
    ) -> None:
        self.env = env
        self.ast = ast
        self.name = name
        self.path = path
        self.global_data = global_data
        self.overlay_data = overlay_data

    def render(self, *args: Any, **kwargs: Any) -> str:
        """Render this template with _args_ and _kwargs_ included in the render context."""
        buf = StringIO()  # TODO: limited buffer
        context = RenderContext(self)
        self.render_with_context(context, buf)
        return buf.getvalue()

    def render_with_context(self, context: RenderContext, buf: TextIO) -> None:
        """Render this template using an existing render context and output buffer."""
        for node in self.ast.nodes:
            node.render(context, buf)
