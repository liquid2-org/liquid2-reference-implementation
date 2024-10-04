"""A parsed template, ready to be rendered."""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING
from typing import Any
from typing import Mapping
from typing import TextIO

from .context import RenderContext
from .exceptions import LiquidInterrupt
from .exceptions import LiquidSyntaxError
from .utils import ReadOnlyChainMap

if TYPE_CHECKING:
    from pathlib import Path

    from .ast import Node
    from .environment import Environment
    from .loader import UpToDate


class Template:
    """A parsed template ready to be rendered."""

    __slots__ = (
        "env",
        "nodes",
        "name",
        "path",
        "global_data",
        "overlay_data",
        "uptodate",
    )

    def __init__(
        self,
        env: Environment,
        nodes: list[Node],
        *,
        name: str = "<string>",
        path: str | Path | None = None,
        global_data: Mapping[str, object] | None = None,
        overlay_data: Mapping[str, object] | None = None,
    ) -> None:
        self.env = env
        self.nodes = nodes
        self.name = name
        self.path = path
        self.global_data = global_data or {}
        self.overlay_data = overlay_data or {}
        self.uptodate: UpToDate = None

    def render(self, *args: Any, **kwargs: Any) -> str:
        """Render this template with _args_ and _kwargs_."""
        buf = StringIO()  # TODO: limited buffer
        context = RenderContext(
            self,
            global_data=self.make_globals(dict(*args, **kwargs)),
        )
        self.render_with_context(context, buf)
        return buf.getvalue()

    def render_with_context(
        self,
        context: RenderContext,
        buf: TextIO,
        *args: Any,
        partial: bool = False,
        **kwargs: Any,
    ) -> None:
        """Render this template using an existing render context and output buffer."""
        # TODO: partial?
        namespace = dict(*args, **kwargs)

        with context.extend(namespace):
            for node in self.nodes:
                try:
                    node.render(context, buf)
                except LiquidInterrupt as err:
                    if not partial:
                        raise LiquidSyntaxError(
                            f"unexpected '{err}'", token=node.token
                        ) from err
                    raise

    def make_globals(self, render_args: Mapping[str, object]) -> Mapping[str, object]:
        """Return a mapping including render arguments and template globals."""
        return ReadOnlyChainMap(
            render_args,
            self.global_data,
            self.overlay_data,
        )
