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
from sicds.loggers import TmpLogger

class TmpStore(BaseStore, TmpLogger):
    '''
    Stores records in memory. All records are lost when the object is destroyed.
    '''
    def __init__(self, *args):
        TmpLogger.__init__(self)
        self.db = set()
        self.keys = set()

    @staticmethod
    def _new_difs_record(id):
        return id

    def _add_difs_records(self, records):
        records = set(records)
        uniq = not self.db.intersection(records)
        self.db.update(records)
        return uniq

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
