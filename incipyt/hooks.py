"""Agnostic hook classes."""
import logging


logger = logging.getLogger(__name__)


class BuildDependancy:
    """Hook to add a dev dependancy to a build system."""

    _hooks = []

    @classmethod
    def register(cls, hook):
        """Regsiter a callback for :class:`BuildDependancy` hook.

        :param hook: Callaback to register.
        :type hook: :class:`collections.abc.Callable`
        """
        cls._hooks.append(hook)

    def __init__(self, hierarchy):
        self._hierarchy = hierarchy

    def __str__(self):
        return "build-dependancy"

    def __call__(self, value):  # noqa: D102
        if self._hooks:
            logger.info(f"{len(self._hooks)} {self} hooks called with '{value}'")

        for hook in self._hooks:
            hook(self._hierarchy, value)


class Classifier:
    """Hook to add a classifier to a build system."""

    _hooks = []

    @classmethod
    def register(cls, hook):
        """Regsiter a callback for :class:`Classifier` hook.

        :param hook: Callaback to register.
        :type hook: :class:`collections.abc.Callable`
        """
        cls._hooks.append(hook)

    def __init__(self, hierarchy):
        self._hierarchy = hierarchy

    def __str__(self):
        return "classifier"

    def __call__(self, value):  # noqa: D102
        if self._hooks:
            logger.info(f"{len(self._hooks)} {self} hooks called with '{value}'")

        for hook in self._hooks:
            hook(self._hierarchy, value)


class ProjectURL:
    """Hook to add a project url to a build system."""

    _hooks = []

    @classmethod
    def register(cls, hook):
        """Regsiter a callback for :class:`ProjectURL` hook.

        :param hook: Callaback to register.
        :type hook: :class:`collections.abc.Callable`
        """
        cls._hooks.append(hook)

    def __init__(self, hierarchy):
        self._hierarchy = hierarchy

    def __str__(self):
        return "project-url"

    def __call__(self, url_kind, url_value):  # noqa: D102
        if self._hooks:
            logger.info(
                f"{len(self._hooks)} {self} hooks called with '{url_kind}: {url_value}'"
            )

        for hook in self._hooks:
            hook(self._hierarchy, url_kind, url_value)


class VCSIgnore:
    """Hook to add a pattern to be ignored by the VCS system."""

    _hooks = []

    @classmethod
    def register(cls, hook):
        """Regsiter a callback for :class:`VCSIgnore` hook.

        :param hook: Callaback to register.
        :type hook: :class:`collections.abc.Callable`
        """
        cls._hooks.append(hook)

    def __init__(self, hierarchy):
        self._hierarchy = hierarchy

    def __str__(self):
        return "vcs-ignore"

    def __call__(self, value):  # noqa: D102
        if self._hooks:
            logger.info(f"{len(self._hooks)} {self} hooks called with '{value}'")

        for hook in self._hooks:
            hook(self._hierarchy, value)
