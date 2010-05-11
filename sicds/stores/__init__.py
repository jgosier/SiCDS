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

from sicds.base import BaseStore, as_tuples
from sicds.stores.couchdb_dbg import CouchStoreDbg
from sicds.stores.mongodb_dbg import MongoStoreDbg

class TmpStore(BaseStore):
    '''
    Stores difs in memory.
    Everything is lost when the object is destroyed.
    '''
    def __init__(self, *args):
        self.db = {}
        self._log_entries = []

    def check(self, key, difs):
        difs = as_tuples(difs)
        if difs in self.db[key]:
            return False
        self.db[key].add(difs)
        return True

    def register_key(self, newkey):
        if newkey in self.db:
            return False
        self.db[newkey] = set()
        return True

    def ensure_keys(self, keys):
        for key in keys:
            if key not in self.db:
                self.db[key] = set()

    def clear(self):
        self.db.clear()

    def _append_log(self, entry):
        self._log_entries.append(entry)
