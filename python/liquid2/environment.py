"""Template parsing and rendering configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Callable
from typing import Mapping
from typing import Type

from _liquid2 import parse

from ._ast import AST
from .builtin import register_standard_tags_and_filters
from .template import Template
from .undefined import Undefined

if TYPE_CHECKING:
    from pathlib import Path


class Environment:
    """Template parsing and rendering configuration."""

    auto_escape = False
    context_depth_limit = 30
    undefined: Type[Undefined] = Undefined

    def __init__(self) -> None:
        self.filters: dict[str, Callable[..., object]] = {}
        register_standard_tags_and_filters(self)

    def parse(self, source: str) -> AST:
        """Compile template source text and return an abstract syntax tree."""
        return AST(self, parse(source))

    def from_string(
        self,
        source: str,
        name: str = "<string>",
        path: str | Path | None = None,
        global_context_data: Mapping[str, object] | None = None,
        overlay_context_data: Mapping[str, object] | None = None,
    ) -> Template:
        """Create a template from a string."""
        return Template(
            self,
            self.parse(source),
            name=name,
            path=path,
            global_data=global_context_data,
            overlay_data=overlay_context_data,
        )
