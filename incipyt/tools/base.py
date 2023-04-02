from abc import ABC, abstractmethod


class Tool(ABC):
    """Base Class for any `Tool`. Concrete `Tool` should subclass it."""

    @abstractmethod
    def add_to_structure(self):
        """Add this Tool's configuration and template to project structure`."""

    def __repr__(self):
        return self.__class__.__name__

    @abstractmethod
    def pre(self, workon):
        """Pre-script, done after creating all folders.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """

    @abstractmethod
    def post(self, workon):
        """Post-script, done before writting configuration and template files.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
