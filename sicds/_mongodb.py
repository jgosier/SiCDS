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
    #: the name of the collection that stores log entries
    cLOG = u'logentries'
    #: the name of the collection that stores the single api-keys document
    cKEYS = u'keys'
    #: collections of difs are named by this prefix and their corresponding key
    cKEYPREFIX = u'KEY:'
    #: the key in the dif documents that maps to the value
    kDIFS = u'difs'

    def __init__(self, url):
        from pymongo import Connection
        host = url.hostname
        port = url.port
        self.conn = Connection(host=host, port=port)
        self.dbid = url.path.split('/')[1]
        self.db = self.conn[self.dbid]
        self._bootstrap()

    def _bootstrap(self):
        self.logc = self.db[self.cLOG]
        self.logc.ensure_index(self.LOG_INDEX)
        self.keyc = self.db[self.cKEYS]
        if not self.keyc.find_one():
            self.keyc.insert({self.kKEYS: []})
        self.difc_by_key = {}
        for key in self.keyc.find_one()[self.kKEYS]:
            difc = self.db[self.cKEYPREFIX + key]
            difc.ensure_index(self.kDIFS, unique=True)
            self.difc_by_key[key] = difc

    @staticmethod
    def _serialize(key, difs):
        return as_tuples(difs)

    def check(self, key, difs):
        s = self._serialize(key, difs)
        difc = self.difc_by_key[key]
        if list(difc.find({self.kDIFS: s}, limit=1)):
            return False
        doc = self._as_doc(key, difs)
        difc.insert(doc)
        return True

    def register_key(self, newkey):
        key = self.cKEYPREFIX + newkey
        if key in self.db.collection_names():
            return False
        difc = self.db[key]
        difc.ensure_index(self.kDIFS, unique=True)
        self.difc_by_key[newkey] = difc
        return True

    def ensure_keys(self, keys):
        kp = self.cKEYPREFIX
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

    def _append_log(self, entry):
        self.logc.insert(entry)
