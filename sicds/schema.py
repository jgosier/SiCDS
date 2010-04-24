from configexc import UrlInitFailure
from functools import wraps
from itertools import chain

class SchemaError(Exception): pass
class MissingField(SchemaError, KeyError): pass
class InvalidField(SchemaError, TypeError): pass
class EmptyField(SchemaError, ValueError): pass
class ExtraFields(SchemaError): pass

class Schema(object):
    '''
    Subclasses specify required and optional fieldname->validator mappings to
    create a corresponding schema. Validators should raise an Exception if
    given invalid values, and return a valid value otherwise. When called with
    no arguments, validators should return a default value.

    The constructor will process the given mapping, raising an exception if it
    does not fulfill the schema, and setting the specified attributes on itself
    otherwise.

    Example::

        >>> class Name(Schema):
        ...     required = {'last': str}
        ...     optional = {'first': str}

        >>> class StreetAddress(Schema):
        ...     required = {'number': int, 'street': str}

        >>> class CityStateZip(Schema):
        ...     required = {'city': str, 'state': str, 'zip': str}

    Schemas are composable::

        >>> class MailingAddress(Schema):
        ...     required = {'name': Name, 'line1': StreetAddress,
        ...                 'line2': CityStateZip}

    Let's test these out::

        >>> name = Name({'first': 'Homer'})
        Traceback (most recent call last):
          ...
        MissingField: 'last'

        >>> name = Name({'first': 'Homer', 'last': 'Simpson', 'middle': 'J'})
        Traceback (most recent call last):
          ...
        ExtraFields: {'middle': 'J'}

        >>> name = Name({'first': 'Homer', 'last': 'Simpson'})
        >>> name
        <Name first=Homer last=Simpson>

        >>> name = Name({'last': 'Simpson'}) # 'first' is optional
        >>> name
        <Name first= last=Simpson>

    The mapping used to build the instance can be recovered::

        >>> name._mapping
        {'last': 'Simpson'}

        >>> line1 = StreetAddress({'number': 'abc', 'street': 'xyz'})
        Traceback (most recent call last):
          ...
        InvalidField: ('number', 'abc')

        >>> line1 = StreetAddress(
        ...     {'number': '742', 'street': 'Evergreen Terrace'})
        >>> line1.number, line1.street
        (742, 'Evergreen Terrace')

    Note ``line1.number`` was processed as an ``int``. We'd probably want
    better validators for state and zip, but for now any string is okay::

        >>> line2 = CityStateZip(
        ...     {'city': 'Springfield', 'state': '?', 'zip': '?'})

    Now for a compound schema::

        >>> address = MailingAddress({
        ...     'name': name._mapping,
        ...     'line1': line1._mapping,
        ...     'line2': line2._mapping,
        ...     })

    Validated. You can verify the subschemas' mappings round-tripped::

        >>> address.line2.city
        'Springfield'

    Here's an invalid compound schema::

        >>> address = MailingAddress({
        ...     'name': name._mapping,
        ...     'line1': line1._mapping,
        ...     'line2': CityStateZip({'invalid': 'data'}),
        ...     })
        Traceback (most recent call last):
          ...
        MissingField...

    '''
    required = {}
    optional = {}
    def __init__(self, mapping):
        self._mapping = dict(mapping) # copy initial config

        def validate(validator, value):
            try:
                return validator(value)
            except EmptyField:
                raise EmptyField(fieldname)
            except UrlInitFailure:
                raise UrlInitFailure(value)
            except:
                raise InvalidField(fieldname, value)

        for fieldname, validator in self.required.iteritems():
            try:
                value = mapping.pop(fieldname)
            except KeyError:
                raise MissingField(fieldname)
            else:
                value = validate(validator, value)
            setattr(self, fieldname, value)

        for fieldname, validator in self.optional.iteritems():
            try:
                value = mapping.pop(fieldname)
            except KeyError:
                value = validator() # no args for default value
            else:
                value = validate(validator, value)
            setattr(self, fieldname, value)

        if mapping:
            raise ExtraFields(mapping)

    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__,
            ' '.join('{0}={1}'.format(k, getattr(self, k))
            for k in sorted(chain(self.required, self.optional))))

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

t_str, t_uni, t_int = [nonfalse(i) for i in (str, unicode, int)]

def withdefault(validator, default):
    '''
    Wraps a validator you do not want to call with no arguments and returns
    the given ``default`` value in this case.

    Useful for optional fields::

        >>> class App(Schema):
        ...     optional = {
        ...         'host': withdefault(str, 'localhost'),
        ...         'port': withdefault(int, 8080),
        ...         }
        >>> app = App({})
        >>> app.host
        'localhost'
        >>> app.port
        8080
        >>> app = App({'port': 1234})
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
