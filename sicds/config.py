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

from _couchdb import CouchStore#, CouchLogger
from _mongodb import MongoStore#, MongoLogger
from base import TmpStore, UrlInitable
from loggers import TmpLogger, NullLogger, FileLogger, StdOutLogger
from schema import Schema, SchemaError, many, t_str, withdefault
from urlparse import urlsplit

DEFAULTKEY = 'sicds_default_key'
DEFAULTSUPERKEY = 'sicds_default_superkey'
DEFAULTHOST = 'localhost'
DEFAULTPORT = 8625
DEFAULTCONFIG = dict(
    host=DEFAULTHOST,
    port=DEFAULTPORT,
    keys=[DEFAULTKEY],
    superkey=DEFAULTSUPERKEY,
    store='tmp:',
    loggers=['file:///dev/stdout'],
    )

#DIFSTORES = {
#    None: TmpStore, # default if not specified
#    'tmp': TmpStore,
#    'couchdb': CouchStore,
#    'mongodb': MongoStore,
#    }

STORES = {
    None: TmpStore, # default if not specified
    'tmp': TmpStore,
    'couchdb': CouchStore,
    'mongodb': MongoStore,
    }

LOGGERS = {
    None: StdOutLogger, # default if not specified
    'tmp': TmpLogger,
    'null': NullLogger,
    'file': FileLogger,
#    'couchdb': CouchLogger,
#    'mongodb': MongoLogger,
    }

#BACKENDS = {
#    'couchdb': {'difstore': CouchStore, 'logger': CouchLogger},
#    'mongodb': {'difstore': MongoStore, 'logger': MongoLogger},
#    }

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
    url = urlsplit(url) if url else None
    scheme = url.scheme if url else None
    try:
        try:
            Class = urlscheme2type[scheme]
        except KeyError:
            raise UnknownUrlScheme(scheme)
        #assert issubclass(Class, UrlInitable)
        return Class(url)
    except:
        raise UrlInitFailure(url) 

def store_from_url(url):
    return _instance_from_url(url, STORES)

def logger_from_url(url):
    return _instance_from_url(url, LOGGERS)

class SiCDSConfig(Schema):
    required = {
        'keys': many(t_str, atleast=1),
        'superkey': t_str,
        'store': store_from_url,
        }
    optional = {
        'host': withdefault(str, DEFAULTHOST),
        'port': withdefault(int, DEFAULTPORT),
        'loggers': withdefault(many(logger_from_url), [StdOutLogger()]),
        }
