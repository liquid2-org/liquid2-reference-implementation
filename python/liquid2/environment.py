"""Template parsing and rendering configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Callable
from typing import ClassVar
from typing import Mapping
from typing import Type

from _liquid2 import LiquidExtensionError as _LiquidExtensionError
from _liquid2 import LiquidNameError as _LiquidNameError
from _liquid2 import LiquidSyntaxError as _LiquidSyntaxError
from _liquid2 import LiquidTypeError as _LiquidTypeError
from _liquid2 import Whitespace
from _liquid2 import tokenize

from .builtin import DictLoader
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
    from .context import RenderContext
    from .loader import BaseLoader
    from .tag import Tag


class Environment:
    """Template parsing and rendering configuration."""

    trim = Whitespace.Plus

    # Maximum number of times a context can be extended or wrapped before raising
    # a ContextDepthError.
    context_depth_limit: ClassVar[int] = 30

    # Maximum number of loop iterations allowed before a LoopIterationLimitError is
    # raised.
    loop_iteration_limit: ClassVar[int | None] = None

    # Maximum number of bytes (according to sys.getsizeof) allowed in a template's
    # local namespace before a LocalNamespaceLimitError is raised. We only count the
    # size of the namespaces values, not the size of keys/names.
    local_namespace_limit: ClassVar[int | None] = None

    # Maximum number of bytes that can be written to a template's output stream before
    # raising an OutputStreamLimitError.
    output_stream_limit: ClassVar[int | None] = None

    template_class = Template

    def __init__(
        self,
        *,
        loader: BaseLoader | None = None,
        global_context_data: Mapping[str, object] | None = None,
        auto_escape: bool = False,
        undefined: Type[Undefined] = Undefined,
    ) -> None:
        self.loader = loader or DictLoader({})
        self.global_context_data = global_context_data or {}
        self.auto_escape = auto_escape
        self.undefined = undefined

        self.filters: dict[str, Callable[..., object]] = {}
        self.tags: dict[str, Tag] = {}
        register_standard_tags_and_filters(self)

        self.parser = Parser(self)

        # TODO: raise if trim is set to "Default"
        # TODO: limits
        # TODO: template_class
        # TODO: setup tags and filters

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
        *,
        name: str = "<string>",
        path: str | Path | None = None,
        global_context_data: Mapping[str, object] | None = None,
        overlay_context_data: Mapping[str, object] | None = None,
    ) -> Template:
        """Create a template from a string."""
        return self.template_class(
            self,
            self.parse(source),
            name=name,
            path=path,
            global_data=global_context_data,
            overlay_data=overlay_context_data,
        )

    def get_template(
        self,
        name: str,
        *,
        global_context_data: Mapping[str, object] | None = None,
        context: RenderContext | None = None,
        **kwargs: object,
    ) -> Template:
        """Load and parse a template using the configured loader.

        Args:
            name: The template's name. The loader is responsible for interpreting
                the name. It could be the name of a file or some other identifier.
            global_context_data: A mapping of render context variables attached to the
                resulting template.
            context: An optional render context that can be used to narrow the template
                source search space.
            kwargs: Arbitrary arguments that can be used to narrow the template source
                search space.

        Raises:
            TemplateNotFound: If a template with the given name can not be found.
        """
        return self.loader.load(
            env=self,
            name=name,
            global_context_data=self.make_globals(global_context_data),
            context=context,
            **kwargs,  # type: ignore
        )

    async def get_template_async(
        self,
        name: str,
        *,
        global_context_data: Mapping[str, object] | None = None,
        context: RenderContext | None = None,
        **kwargs: object,
    ) -> Template:
        """An async version of `get_template()`."""
        return await self.loader.load_async(
            env=self,
            name=name,
            global_context_data=self.make_globals(global_context_data),
            context=context,
            **kwargs,  # type: ignore
        )

    def make_globals(
        self,
        globals: Mapping[str, object] | None = None,  # noqa: A002
    ) -> dict[str, object]:
        """Combine environment globals with template globals."""
        if globals:
            # Template globals take priority over environment globals.
            return {**self.global_context_data, **globals}
        return dict(self.global_context_data)
