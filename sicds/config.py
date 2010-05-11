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

from sicds.base import UrlInitable
from sicds.loggers import NullLogger, FileLogger, StdOutLogger
from sicds.schema import Reference, Schema, SchemaError, many, \
    withdefault, t_uni
from sicds.stores import TmpStore, CouchStore, MongoStore
from urlparse import urlsplit

DEFAULTCONFIG = dict(
    host='localhost',
    port=8625,
    keys=['sicds_default_key'],
    superkey='sicds_default_superkey',
    store='tmp:',
    )

STORES = {
    'tmp': TmpStore,
    'couchdb': CouchStore,
    'mongodb': MongoStore,
    }

LOGGERS = {
    'null': NullLogger,
    'file': FileLogger,
    'store': Reference('store'), # use whatever was configured as the store
    }

class ConfigError(SchemaError): pass
class UnknownUrlScheme(ConfigError): pass
class UrlInitFailure(ConfigError): pass

def _instance_from_url(url, urlscheme2type):
    '''
    Returns a new UrlInitable object designated by the given url and
    urlscheme2type mapping.

        >>> null_logger = _instance_from_url('null:', LOGGERS)
        >>> isinstance(null_logger, NullLogger)
        True

    '''
    # assume urlsplit correctly handles novel schemes
    # this requires at least Python 2.6.5!
    # see http://bugs.python.org/issue7904
    url = urlsplit(url)
    scheme = url.scheme
    try:
        try:
            Class = urlscheme2type[scheme]
        except KeyError:
            raise UnknownUrlScheme(scheme)
        if isinstance(Class, Reference):
            return Class
        return Class(url)
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
