# Copyright (C) 2012 by Kevin L. Mitchell <klmitch@mit.edu>
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see
# <http://www.gnu.org/licenses/>.

import functools
import inspect


class Translators(object):
    """
    Represent a set of translators.  A translator is a serializer or
    deserializer, corresponding to a particular return type.
    """

    def __init__(self, method, attr_name):
        """
        Initialize a set of translators.  The translators for a given
        method are derived from the class of the method, updated with
        translators set on the method itself.  The `attr_name`
        parameter specifies the attribute containing the translation
        table.
        """

        # Build up the translators
        self.translators = getattr(method.im_self, attr_name, {}).copy()
        self.translators.update(getattr(method, attr_name, {}))

    def __call__(self, content_type):
        """
        Select the translator corresponding to the given content type.
        """

        # Select the translator to use
        xlator = self.translators[media_types[content_type]]

        # If it's a class, instantiate it
        if inspect.isclass(xlator):
            return xlator(type_name, content_type)

        # It's a function; partialize and return it
        return functools.partial(xlator, type_name, content_type)

    def get_types(self):
        """
        Retrieve a set of all recognized content types for this
        translator object.
        """

        # Convert translators into a set of content types
        content_types = set()
        for name in self.translators:
            content_types |= type_names[name]

        return content_types


def _translators(attr, kwargs):
    """
    Decorator which associates a set of translators (serializers or
    deserializers) with a given method.  The `attr` parameter
    identifies which attribute is being updated.
    """

    # Add translators to a function or class
    def decorator(func):
        xlators = func.__dict__.setdefault(attr, {})
        xlators.update(kwargs)
        return func
    return decorator


def serializers(**kwargs):
    """
    Decorator which binds a set of serializers with a method.  The key
    of each keyword argument is interpreted as a short name for the
    content type (bind short names to content types using
    register_types()), and the value is a callable.

    If the callable is a class, it will be instantiated with two
    arguments: the short type name and the content type.  It must
    define a __call__() method taking one argument: the object to
    serialize.  The class may also define an optional attach() method,
    which allows serializers for extensions to be attached to the
    primary serializer.

    If the callable is a function, it will be called with three
    arguments: the short type name, the content type, and the object
    to serialize.
    """

    return _translators('_wsgi_serializers', kwargs)


def deserializers(**kwargs):
    """
    Decorator which binds a set of deserializers with a method.  The
    key of each keyword argument is interpreted as a short name for
    the content type (bind short names to content types using
    register_types()), and the value is a callable.

    If the callable is a class, it will be instantiated with two
    arguments: the short type name and the content type.  It must
    define a __call__() method taking one argument: the string to
    deserialize.  The class may also define an optional attach()
    method, which allows deserializers for extensions to be attached
    to the primary deserializer.

    If the callable is a function, it will be called with three
    arguments: the short type name, the content type, and the string
    to deserialize.
    """

    return _translators('_wsgi_deserializers', kwargs)


media_types = {}
type_names = {}


def register_types(name, *types):
    """
    Register a short name for one or more content types.
    """

    type_names.setdefault(name, set())
    for t in types:
        # Redirecting the type
        if t in media_types:
            type_names[media_types[t]].discard(t)

        # Save the mapping
        media_types[t] = name
        type_names[name].add(t)
