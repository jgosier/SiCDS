#!/usr/bin/env python
# Copyright (C) 2010 Ushahidi Inc. <jon@ushahidi.com>,
# Joshua Bronson <jabronson@gmail.com>, and contributors
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301
# USA

from functools import wraps
from itertools import chain

class SchemaError(Exception): pass
class RequiredField(SchemaError): pass
class InvalidField(SchemaError): pass
class EmptyField(SchemaError): pass
class ExtraFields(SchemaError): pass
class ReferenceError(SchemaError): pass

class Schema(object):
    '''
    Subclasses specify required and optional field->validator mappings to
    create a corresponding schema. Validators should raise an Exception if
    given invalid values, and return a valid value otherwise. When called with
    no arguments, validators should return a default value.

    The constructor will process the given mappings, raising an exception if it
    does not fulfill the schema, and setting the specified fields as attributes
    on itself otherwise.

    Example::

        >>> class Name(Schema):
        ...     required = {'last': str}
        ...     optional = {'first': str}

        >>> class Address(Schema):
        ...     required = {'number': int, 'street': str}

    Schemas are composable::

        >>> class ContactInfo(Schema):
        ...     required = {'name': Name, 'address': Address}

    Let's test these out::

        >>> name = Name(first='Homer')
        Traceback (most recent call last):
          ...
        RequiredField: last

        >>> name = Name(first='Homer', last='Simpson', middle='J')
        Traceback (most recent call last):
          ...
        ExtraFields: middle

        >>> name = Name(first='Homer', last='Simpson')
        >>> name
        <Name first='Homer' last='Simpson'>

    You can get or set fields through attribute access:

        >>> name.first
        'Homer'
        >>> name.first = 'Lisa'
        >>> name
        <Name first='Lisa' last='Simpson'>

    But only fields that are part of the schema::

        >>> name.suffix = 'not part of the schema!'
        Traceback (most recent call last):
          ...
        ExtraFields: suffix

    You can delete fields too, but only if they're optional. This causes the
    field to be reset to its default value::

        >>> del name.first
        >>> name.first
        ''
        >>> del name.last
        Traceback (most recent call last):
          ...
        RequiredField: last

    Equivalence comparison works with other Schema instances as well as dicts::

        >>> name == Name(last='Simpson') == {'last': 'Simpson'}
        True

    You can unwrap the mapping underpinning the instance like::

        >>> name.unwrap
        {...'last': 'Simpson'...}


    Let's demonstrate invalid fields::

        >>> addr = Address(number='abc', street='xyz')
        Traceback (most recent call last):
          ...
        InvalidField: ('number', 'abc')

        >>> address = Address(number='742', street='Evergreen Terrace')
        >>> address
        <Address number=742 street='Evergreen Terrace'>

    Validation is triggered on setattr as well::
        
        >>> address.number = 'not a number'
        Traceback (most recent call last):
          ...
        InvalidField: ('number', 'not a number')
    
    Now let's demonstrate the compound schema::

        >>> ContactInfo(name=Name(last='Nahasapeemapetilon'))
        Traceback (most recent call last):
          ...
        RequiredField: address

    Here's a valid one, using our already-validated instances::

        >>> info = ContactInfo(name=name, address=address)

    You can descend into subschemas::

        >>> info.address.number
        742

    And unwrapping the compound schema unwraps its subschemas::

        >>> info.unwrap
        {...'name': {...'last': 'Simpson'...}...}

    The round-trip::

        >>> ContactInfo(info.unwrap) == info
        True

    '''
    required = {}
    optional = {}

    def _validate(self, field, validator, value):
        value = unwrap(value)
        try:
            value = validator(value)
        except EmptyField:
            raise EmptyField(field)
        except SchemaError:
            raise
        except Exception as e:
            raise InvalidField(field, value)
        return value

    def __init__(self, *args, **kw):
        values = dict(*args, **kw)
        for field, validator in chain(
                self.required.iteritems(), self.optional.iteritems()):
            try:
                value = values.pop(field)
            except KeyError:
                if field in self.required:
                    raise RequiredField(field)
                # field is optional, use default value
                value = validator() # call with no args for default value
            else:
                value = self._validate(field, validator, value)
            value = dereference(value, self)
            object.__setattr__(self, field, value)

        if values:
            raise ExtraFields(', '.join(values.iterkeys()))

        defaults = dict((field, validator()) for \
            (field, validator) in self.optional.iteritems())
        object.__setattr__(self, '_defaults', defaults)

    def __setattr__(self, attr, value):
        try:
            validator = self.required[attr]
        except KeyError:
            try:
                validator = self.optional[attr]
            except KeyError:
                raise ExtraFields(attr)
        value = self._validate(attr, validator, value)
        object.__setattr__(self, attr, value)

    def __delattr__(self, attr):
        if attr in self.required:
            raise RequiredField(attr)
        default = self._defaults[attr]
        object.__setattr__(self, attr, default)

    @property
    def unwrap(self):
        return unwrap(self)

    def __eq__(self, other):
        other = unwrap(other)
        if isinstance(other, dict):
            other = dict(self._defaults, **other)
        return unwrap(self) == other

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__,
            ' '.join('{0}={1}'.format(field, repr(value)) for \
            (field, value) in sorted(self.unwrap.iteritems())))

def unwrap(x):
    if isinstance(x, Schema):
        return dict((field, unwrap(getattr(x, field)))
            for field in chain(x.required, x.optional))
    if isinstance(x, dict):
        return dict((k, unwrap(v)) for (k, v) in x.iteritems())
    if isinstance(x, basestring):
        return x
    try:
        return [unwrap(i) for i in x]
    except:
        return x

class Reference(object):
    def __init__(self, field):
        self.field = field

def dereference(x, referent):
    if isinstance(x, Reference):
        return getattr(referent, x.field)
    if isinstance(x, dict):
        return dict((k, dereference(v, referent)) for (k, v) in x.iteritems())
    if isinstance(x, basestring):
        return x
    try:
        return [dereference(i, referent) for i in x]
    except:
        return x

def nonfalse(validator):
    '''
    Wraps a validator in a function that checks the result for its truth value
    before returning it.

    :raises: :exc:`EmptyField`

    >>> nonemptystr = nonfalse(str)
    >>> nonemptystr('nonempty')
    'nonempty'
    >>> nonemptystr('')
    Traceback (most recent call last):
      ...
    EmptyField...
    '''
    @wraps(validator)
    def wrapper(arg):
        result = validator(arg)
        if not result:
            raise EmptyField
        return result
    return wrapper

t_uni, t_int = [nonfalse(i) for i in (unicode, int)]

def withdefault(validator, default):
    '''
    Wraps a validator you do not want to call with no arguments and returns
    the given default value when called with no args.

    Useful for optional fields::

        >>> class App(Schema):
        ...     optional = {
        ...         'host': withdefault(str, 'localhost'),
        ...         'port': withdefault(int, 8080),
        ...         }
        >>> app = App()
        >>> app.host
        'localhost'
        >>> app.port
        8080
        >>> app = App(port=1234)
        >>> app.port
        1234

    '''
    @wraps(validator)
    def wrapper(*args):
        if not args:
            return default
        return validator(*args)
    return wrapper

def many(validator, uniq=False, atleast=None):
    '''
    Wraps a validator in a function that applies it to items in an iterable
    and returns the result. Specify ``uniq=True`` to filter duplicate values.
    Specify ``atleast`` to ensure the resulting list has at least that many
    elements.

    :raises: :exc:`InvalidField`

    >>> intifyseq = many(int)
    >>> intifyseq(('1', '2', '3'))
    [1, 2, 3]
    >>> intifyseq([])
    []
    >>> atleast3uniq = many(int, uniq=True, atleast=3)
    >>> atleast3uniq(('1', '2', '2'))
    Traceback (most recent call last):
      ...
    InvalidField...
    '''
    @wraps(validator)
    def wrapper(iterable):
        result = [validator(i) for i in iterable]
        if uniq:
            result = list(set(result))
        if atleast is not None and len(result) < atleast:
            raise InvalidField
        return result
    return wrapper


if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
