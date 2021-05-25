class Action:
    """Base Class for any `Action`. Concrete `Action` should subclass it."""

    def add_to(self, hierarchy):
        """Add this action's configuration and template to `hierarchy`.

        :param hierarchy: The actual hierarchy to update with this action
        :type hierarchy: :class:`incipyt.system.Hierarchy`
        """

    def __repr__(self):
        return self.__class__.__name__

    def pre(self, workon, environment):
        """Pre-action, do after creating all folders.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        :param environment: Environment used to do pre-action
        :type environment: :class:`incipyt.system.Environment`
        """

    def post(self, workon, environment):
        """Pre-action, do before writting configuration and template files.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        :param environment: Environment used to do post-action
        :type environment: :class:`incipyt.system.Environment`
        """
