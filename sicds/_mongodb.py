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

from sicds.base import DocStore, as_tuples

class MongoStore(DocStore):
    kDIFS = 'difs'
    _KEYPREFIX = u'KEY:'

    def __init__(self, url):
        from pymongo import Connection
        host = url.hostname
        port = url.port
        self.conn = Connection(host=host, port=port)
        self.dbid = url.path.split('/')[1]
        self.db = self.conn[self.dbid]
        self._bootstrap()

    def _bootstrap(self):
        self.keyc = self.db[self.kKEYS]
        if not self.keyc.find_one():
            self.keyc.insert({self.kKEYS: []})
        self.difc_by_key = {}
        for key in self.keyc.find_one()[self.kKEYS]:
            difc = self.db[self._KEYPREFIX + key]
            difc.ensure_index(self.kDIFS, unique=True)
            self.difc_by_key[key] = difc

    def has(self, key, difs):
        doc = {self.kDIFS: as_tuples(difs)}
        difc = self.difc_by_key[key]
        return bool(difc.find_one(doc))

    def add(self, key, difs):
        doc = {self.kDIFS: as_tuples(difs)}
        difc = self.difc_by_key[key]
        difc.insert(doc)

    def register_key(self, newkey):
        if newkey in self.db.collection_names():
            return False
        difc = self.db[self._KEYPREFIX + newkey]
        difc.ensure_index(self.kDIFS, unique=True)
        self.difc_by_key[newkey] = difc
        return True

    def ensure_keys(self, keys):
        kp = self._KEYPREFIX
        n = len(kp)
        newkeys = set(keys) - set(i[n:] for i in \
            self.db.collection_names() if i.startswith(kp))
        for key in newkeys:
            difc = self.db[kp + key]
            difc.ensure_index(self.kDIFS, unique=True)
            self.difc_by_key[key] = difc

    def clear(self):
        self.conn.drop_database(self.db)
        self._bootstrap()

#class MongoLogger(MongoStore, BaseLogger):
#    '''
#    Stores log entries in a MongoDB instance.
#    '''
#    def _store(self, entry):
#        self.collection.insert(entry)
