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

from sicds.base import BaseStore
from sicds.stores.couch import CouchStore
from sicds.stores.mongo import MongoStore

class TmpStore(BaseStore):
    '''
    Stores difs in memory.
    Everything is lost when the object is destroyed.
    '''
    def __init__(self, *args):
        self.db = set()
        self.keys = set()
        self._log_entries = []

    def _filter_old(self, ids):
        return list(self.db.intersection(set(ids)))

    @staticmethod
    def _new_difs_record(id):
        return id

    def _add_difs_records(self, records):
        self.db.update(records)

    def register_key(self, newkey):
        if newkey in self.keys:
            return False
        self.keys.add(newkey)
        return True

    def ensure_keys(self, keys):
        self.keys.update(keys)
        return iter(self.keys)

    def clear(self):
        self.db.clear()

    def _add_log_record(self, record):
        self._log_entries.append(record)
