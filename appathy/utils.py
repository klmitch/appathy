import re
import sys

import pkg_resources


# Regular expression to identify repeated slashes
_path_re = re.compile(r'/{2,}')


def norm_path(path, allow_trailing=True):
    """
    Normalize a route path.  Ensures that the path begins with a '/'.
    If `allow_trailing` is False, strips off any trailing '/'.  Any
    repeated '/' characters in the path will be collapsed into a
    single one.
    """

    # Collapse slashes
    path = _path_re.sub('/', path)

    # Force a leading slash
    if path[0] != '/':
        path = '/' + path

    # Trim a trailing slash
    if not allow_trailing and path[-1] == '/':
        path = path[:-1]

    return path


def import_string(string):
    """
    Import an object identified by a string, using pkg_resources.
    """

    return pkg_resources.EntryPoint.parse("x=" + string).load(False)


def import_object(obj_name):
    """
    Import the specified object given its name.
    """

    # Split cls into a module and an object
    if ':' not in obj_name:
        raise ImportError("Invalid object identifier for import_class()")

    mod_name, full_name = cls_name.split(':', 1)

    # Get the module
    __import__(mod_name)
    mod = sys.modules[mod_name]

    # Look up the class
    obj = mod
    traversed = []
    for part in full_name.split('.'):
        traversed.append(part)
        try:
            obj = getattr(obj, part)
        except AttributeError:
            raise ImportError("Cannot locate object %s in module %s" %
                              ('.'.join(traversed), mod_name))

    return obj
