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

from _couchdb import CouchDifStore, CouchLogger
from _mongodb import MongoDifStore, MongoLogger
from base import TmpDifStore, TmpLogger, NullLogger, FileLogger, StdOutLogger, UrlInitable
from configexc import UnknownUrlScheme, UrlInitFailure
from schema import Schema, SchemaError, many, t_str, withdefault

from urlparse import urlsplit

DEFAULTKEY = 'sicds_test'
DEFAULTHOST = 'localhost'
DEFAULTPORT = 8080
DEFAULTCONFIG = dict(
    host=DEFAULTHOST,
    port=DEFAULTPORT,
    keys=[DEFAULTKEY],
    difstore='tmp:',
    logger='file:///dev/stdout',
    )

DIFSTORES = {
    None: TmpDifStore, # default if not specified
    'tmp': TmpDifStore,
    'couchdb': CouchDifStore,
    'mongodb': MongoDifStore,
    }

LOGGERS = {
    None: StdOutLogger, # default if not specified
    'tmp': TmpLogger,
    'null': NullLogger,
    'file': FileLogger,
    'couchdb': CouchLogger,
    'mongodb': MongoLogger,
    }

def _instance_from_url(urlscheme2type):
    '''
    Returns a new UrlInitable object designated by the given url
    and scheme2type mapping.
    '''
    def wrapper(url=None):
        url = urlsplit(url) if url else None
        scheme = url.scheme if url else None
        try:
            try:
                Class = urlscheme2type[scheme]
            except KeyError:
                raise UnknownUrlScheme(scheme)
            assert issubclass(Class, UrlInitable)
            return Class(url)
        except:
            raise UrlInitFailure(url) 
    return wrapper

difstore_from_url = _instance_from_url(DIFSTORES)
logger_from_url = _instance_from_url(LOGGERS)

class SiCDSConfig(Schema):
    required = {
        'keys': many(t_str, atleast=1),
        'difstore': difstore_from_url,
        }
    optional = {
        'host': withdefault(str, DEFAULTHOST),
        'port': withdefault(int, DEFAULTPORT),
        'logger': logger_from_url,
        }
