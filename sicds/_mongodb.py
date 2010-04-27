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

from base import DocDifStore, BaseLogger, UrlInitable

class MongoStore(UrlInitable):
    def __init__(self, url):
        '''
        Base class for data stores backed by MongoDB. Opens a connection to
        the Mongo database and collection specified in ``url``.
        '''
        from pymongo import Connection
        host = url.hostname
        port = url.port
        self.conn = Connection(host=host, port=port)
        self.dbid, self.collectionid = url.path.split('/')[1:3]
        self.db = self.conn[self.dbid]
        self.collection = self.db[self.collectionid]

class MongoDifStore(MongoStore, DocDifStore):
    '''
    Stores difs in a MongoDB instance.
    '''
    def __init__(self, url):
        MongoStore.__init__(self, url)
        self.collection.ensure_index(self._KEY, unique=True)

    def has(self, key, difs):
        '''
        Returns True iff difs is in the database.
        '''
        doc = self._as_doc(difs)
        return bool(self.collection.find_one(doc))

    def add(self, key, difs):
        '''
        Adds a set of difs to the database.
        '''
        doc = self._as_doc(difs)
        self.collection.insert(doc)

    def clear(self):
        self.db.drop_collection(self.collection)
        self.collection = self.db[self.collectionid]

class MongoLogger(MongoStore, BaseLogger):
    '''
    Stores log entries in a MongoDB instance.
    '''
    def _store(self, entry):
        self.collection.insert(entry)
