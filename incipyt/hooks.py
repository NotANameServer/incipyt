"""TO-DO."""


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

    def __call__(self, value):  # noqa: D102
        for hook in self._hooks:
            hook(self._hierarchy, value)


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

    def __call__(self, value):  # noqa: D102
        for hook in self._hooks:
            hook(self._hierarchy, value)
