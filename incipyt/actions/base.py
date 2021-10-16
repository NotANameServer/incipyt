class Action:
    """Base Class for any `Action`. Concrete `Action` should subclass it."""

    def add_to_structure(self):
        """Add this action's configuration and template to project structure`."""

    def __repr__(self):
        return self.__class__.__name__

    def pre(self, workon):
        """Pre-action, do after creating all folders.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """

    def post(self, workon):
        """Pre-action, do before writting configuration and template files.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
