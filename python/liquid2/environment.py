"""Template parsing and rendering configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Callable
from typing import Mapping
from typing import Type

from _liquid2 import LiquidExtensionError as _LiquidExtensionError
from _liquid2 import LiquidNameError as _LiquidNameError
from _liquid2 import LiquidSyntaxError as _LiquidSyntaxError
from _liquid2 import LiquidTypeError as _LiquidTypeError
from _liquid2 import Whitespace
from _liquid2 import tokenize

from .builtin import register_standard_tags_and_filters
from .exceptions import LiquidError
from .exceptions import LiquidSyntaxError
from .exceptions import LiquidTypeError
from .parser import Parser
from .template import Template
from .undefined import Undefined

if TYPE_CHECKING:
    from pathlib import Path

    from .ast import Node
    from .tag import Tag


class Environment:
    """Template parsing and rendering configuration."""

    auto_escape = False
    context_depth_limit = 30
    trim = Whitespace.Plus
    undefined: Type[Undefined] = Undefined

    def __init__(self) -> None:
        self.filters: dict[str, Callable[..., object]] = {}
        self.tags: dict[str, Tag] = {}
        register_standard_tags_and_filters(self)

        self.parser = Parser(self)

        # TODO: raise if trim is set to "Default"
        # TODO: environment globals
        # TODO: loaders, loaders that handle caching
        # TODO: limits
        # TODO: template_class

    def parse(self, source: str) -> list[Node]:
        """Compile template source text and return an abstract syntax tree."""
        # TODO: pass tokens to exceptions
        # XXX:
        try:
            return self.parser.parse(tokenize(source))
        except _LiquidSyntaxError as err:
            raise LiquidSyntaxError(err, token=None) from err
        except _LiquidTypeError as err:
            raise LiquidTypeError(err, token=None) from err
        except (_LiquidNameError, _LiquidExtensionError) as err:
            raise LiquidError(err, token=None) from err

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
