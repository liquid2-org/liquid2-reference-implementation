"""Template parsing and rendering configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Mapping
from typing import Type

from liquid2 import parse

from ._ast import _AST
from .template import Template
from .undefined import Undefined

if TYPE_CHECKING:
    from pathlib import Path


class Environment:
    """Template parsing and rendering configuration."""

    def __init__(self) -> None:
        self.undefined: Type[Undefined] = Undefined

    def _parse(self, source: str) -> _AST:
        return _AST(self, parse(source))

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
            self._parse(source),
            name=name,
            path=path,
            global_data=global_context_data,
            overlay_data=overlay_context_data,
        )
