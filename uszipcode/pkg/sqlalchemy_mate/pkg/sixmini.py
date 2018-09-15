#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a minimized six model.
"""

import sys
import types

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes

    MAXSIZE = sys.maxsize
else:
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str

    if sys.platform.startswith("java"):
        # Jython always uses 32 bits.
        MAXSIZE = int((1 << 31) - 1)
    else:
        # It's possible to have sizeof(long) != sizeof(Py_ssize_t).
        class X(object):

            def __len__(self):
                return 1 << 31
        try:
            len(X())
        except OverflowError:
            # 32-bit
            MAXSIZE = int((1 << 31) - 1)
        else:
            # 64-bit
            MAXSIZE = int((1 << 63) - 1)
        del X

if PY3:
    def iterkeys(d, **kw):
        return iter(d.keys(**kw))

    def itervalues(d, **kw):
        return iter(d.values(**kw))

    def iteritems(d, **kw):
        return iter(d.items(**kw))

else:
    def iterkeys(d, **kw):
        return d.iterkeys(**kw)

    def itervalues(d, **kw):
        return d.itervalues(**kw)

    def iteritems(d, **kw):
        return d.iteritems(**kw)


def add_metaclass(metaclass):
    """Class decorator for creating a class with a metaclass."""
    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        slots = orig_vars.get('__slots__')
        if slots is not None:
            if isinstance(slots, str):
                slots = [slots]
            for slots_var in slots:
                orig_vars.pop(slots_var)
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper
