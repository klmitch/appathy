==================================
Appathy REST Application Framework
==================================

Appathy is a framework for constructing REST-like web APIs.  Appathy
binds Routes, WebOb, and PasteDeploy together with an easy to use set
of classes and decorators to simplify writing web applications.

The two most important classes in Appathy are the Application and
Controller classes.  The Application class is used as the application
in the PasteDeploy configuration file.  Other configuration items in
the application section of the ``paste.ini`` file tell the Application
class about the available resources and their extensions, both
represented by subclasses of the Controller class.

The Controller class is the workhorse of Appathy.  Each resource or
extension must extend Controller, and must have one or more methods
decorated with either the ``@action()`` or ``@extends`` decorators.
They may also be decorated with the ``@deserializers()`` and
``@serializers()`` decorators to attach request deserializers and
response serializers to the action or extension.

Controller methods decorated with the ``@action()`` decorator specify
a method that will be called when a specific request is received by
the application.  The first argument to ``@action()`` is a URI path,
and any remaining positional arguments identify the matching HTTP
methods (i.e., "GET", "PUT", etc.); if none are provided, the method
will be called for all accesses to the given path.  Two keyword
arguments are also accepted: the ``code`` keyword argument can be used
to specify the default response code (normally 200), and
``conditions`` can be used to specify a function to further filter the
request before selecting the action method.  The action method will be
called with the request and a set of keyword arguments derived from
the URI path and any additional keyword arguments that were passed to
the ``@action()`` decorator.

Controller methods decorated with the ``@extends`` decorator specify a
method that will extend an action method with the same function name
in another controller.  Extension methods come in two varieties:
generator extensions and regular extensions.  A regular extension is a
simple method which is called after the action method has finished; it
is called with the request, the response object, and the keyword
parameters passed to the action method.

Generator extensions, on the other hand, are generator functions
(functions containing at least one ``yield`` statement).  The part of
the generator before the first ``yield`` is executed prior to calling
the action method, and is passed the request and the keyword
parameters which will be passed to the action method.  If a value is
yielded by the generator extension, the action method will not be
called; the value will instead be returned to the caller.  Otherwise,
once the generator expression yields, the action method will be called
as normal, and then the response will be passed to the generator
extension for post processing; this response object will appear as the
result of the ``yield`` statement.  The generator extension may
perform its post-processing at this point.

If a regular extension returns a value or if a generator extension
yields a value during post-processing of a request, that value becomes
the response for the remainder of the processing.  Extensions may also
be stacked, allowing for several extensions to be specified for a
given action.

The action method may return either a simple type (i.e., a number, a
string, a list, or a dictionary), or it may return an instance of
ResponseObject.  The ResponseObject class exists to encapsulate the
simple type and allow extra functionality, such as setting specific
HTTP headers on the response or overriding the response code.  If an
action method returns a simple type, that will be encapsulated in a
ResponseObject before calling any extensions.

The final piece of Appathy is the translators.  "Translators" is a
generic name for request deserializers and response serializers.  A
request deserializer is responsible for reading the body of a request
(e.g., PUT or POST requests) and converting it into the form expected
by the action method (and any extensions), while a response serializer
is responsible for taking the object returned by the action method (or
any extension) and converting it into the form expected by the
application client.  This allows multiple content types to be
understood and handled without having to account for this in the
action method.

A translator is nothing more than a callable.  If the translator is a
simple function, it will be called with the type name (a short name
describing the content type, e.g., "json" or "xml"), the actual
content type (e.g., "application/json"), and the request body or
response object.  If the translator is a class, its constructor will
be called with the first two arguments, and it must implement a
``__call__()`` method which will be passed the third argument.  To
support complex extensions, if the translator class has an
``attach()`` method, the (instantiated) translators for any extensions
will be passed (in an appropriate order) to that method; this could be
used to ensure that a field added by an extension is properly
converted and added to a final response, or to ensure that a field of
a request object consumed by an extension is properly extracted.

The translator system needs to be able to map short names, which are
used by the ``@deserializers()`` and ``@serializers()`` decorators, to
and from MIME content types.  These mappings can be created using the
``register_types()`` function.  At present, Appathy does not provide
any default translators.
