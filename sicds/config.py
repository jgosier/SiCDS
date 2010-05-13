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

from sicds.loggers import StdOutLogger
from sicds.schema import Reference, Schema, SchemaError, many, \
    withdefault, t_uni
from urlparse import urlparse

DEFAULTCONFIG = dict(
    host='localhost',
    port=8625,
    keys=['sicds_default_key'],
    superkey='sicds_default_superkey',
    store='tmp:',
    )

STORES = {
    'tmp': 'sicds.stores.tmp.TmpStore',
    'couchdb': 'sicds.stores.couch.CouchStore',
    'mongodb': 'sicds.stores.mongo.MongoStore',
    }

LOGGERS = {
    'null': 'sicds.loggers.NullLogger',
    'file': 'sicds.loggers.FileLogger',
    'store': Reference('store'), # use whatever was configured as the store
    }

class ConfigError(SchemaError): pass
class UnknownUrlScheme(ConfigError): pass
class UrlInitFailure(ConfigError): pass

def _instance_from_url(url, urlscheme2type):
    '''
    Returns a new UrlInitable object designated by the given url and
    urlscheme2type mapping.

        >>> filelogger = _instance_from_url('file:///dev/stdout',
        ...     {'file': 'sicds.loggers.FileLogger'})
        >>> filelogger.log
        <bound method FileLogger.log of ...>

    '''
    # assume urlparse correctly handles novel schemes
    # this requires at least Python 2.6.5
    # see http://bugs.python.org/issue7904
    parsedurl = urlparse(url)
    scheme = parsedurl.scheme
    try:
        try:
            name = urlscheme2type[scheme]
        except KeyError:
            raise UnknownUrlScheme(scheme)
        if isinstance(name, Reference):
            return name
        modulename, factory = name.rsplit('.', 1)
        module = __import__(modulename)
        for component in modulename.split('.')[1:]:
            module = getattr(module, component)
        factory = getattr(module, factory)
        return factory(parsedurl)
    except:
        raise UrlInitFailure(url) 

def store_from_url(url):
    return _instance_from_url(url, STORES)

def logger_from_url(url):
    return _instance_from_url(url, LOGGERS)

class SiCDSConfig(Schema):
    required = {
        'superkey': t_uni,
        'store': store_from_url,
        }
    optional = {
        'host': str,
        'port': withdefault(int, ''),
        'keys': withdefault(many(t_uni), []),
        'loggers': withdefault(many(logger_from_url), [StdOutLogger()]),
        }

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
