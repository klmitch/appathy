class AppathyException(Exception):
    """Base class for all Appathy exceptions."""

    # A list of argument names for positional arguments to the
    # constructor.  If not provided, the first positional argument
    # (which will be optional) will be the message.
    base_args = None

    def __init__(self, *args, **kwargs):
        """
        Initialize an AppathyException.
        """

        if self.base_args:
            # If base_args is set, interpolate positional arguments
            # into keyword arguments and get the message from the
            # docstring
            message = self.__doc__
            targs = dict(zip(self.base_args, args))
            targs.update(kwargs)
            kwargs = targs
        elif args:
            # Get the message from the first positional argument
            message = args[0]
        else:
            # Get the message from the docstring
            message = self.__doc__

        super(AppathyException, self).__init__(message % kwargs)


class IncompleteController(AppathyException):
    """Cannot instantiate an incomplete controller"""


class DuplicateResource(AppathyException):
    """Resource %(name)r already exists"""

    base_args = ['name']


class NoSuchResource(AppathyException):
    """No such resource %(name)r"""

    base_args = ['name']
