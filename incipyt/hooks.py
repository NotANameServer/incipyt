"""Tool-agnostic hook classes."""
import logging


logger = logging.getLogger(__name__)


class _Hook:
    """Generic hook baseclass. Concrete hooks should subclass it."""

    def __init_subclass__(cls):
        # Each subclass must have its own _hooks attribute
        cls._hooks = []

    def __init__(self, hierarchy):
        self._hierarchy = hierarchy

    def __str__(self):
        return self.__class__.__name__

    def __call__(self, *args):
        """Call registered hooks."""
        if self._hooks:
            logger.info(
                f"{len(self._hooks)} {self} hook(s) called with {self._format_args(args)}"
            )

        for hook in self._hooks:
            hook(self._hierarchy, *args)

    def _format_args(self, args):
        return f"arguments: {args}"

    @classmethod
    def register(cls, hook):
        """Regsiter a callback for a :class:`Hook`.

        :param hook: Callaback to register.
        :type hook: :class:`callable`
        """
        cls._hooks.append(hook)


class _SingleParameterHook(_Hook):
    """Generic Hook subclass whose registered hooks take only one parameter."""

    def __call__(self, value):  # noqa: D102
        super().__call__(value)

    def _format_args(self, args):
        return f"argument: {args[0]}"


class ProjectURL(_Hook):
    """Hook to add a project url to a build system."""

    def __call__(self, url_kind, url_value):  # noqa: D102
        super().__call__(url_kind, url_value)

    def _format_args(self, args):
        return f"argument: {args[0]}: {args[1]}"


class BuildDependancy(_SingleParameterHook):
    """Hook to add a dev dependancy to a build system."""


class Classifier(_SingleParameterHook):
    """Hook to add a classifier to a build system."""


class VCSIgnore(_SingleParameterHook):
    """Hook to add a pattern to be ignored by the VCS system."""
