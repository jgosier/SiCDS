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

from sicds.base import DocStore

class MongoStore(DocStore):
    #: the name of the collection that stores log entries
    cLOG = u'logentries'
    #: the name of the collection that stores the single api-keys document
    cKEYS = u'keys'
    #: the name of the collection that stores the dif documents
    cDIFS = u'difs'

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
        self.difc = self.db[self.cDIFS]

    def __contains__(self, id):
        return bool(self.difc.find_one({u'_id': id}))

    def _add_difs_records(self, records):
        self.difc.insert(records, safe=True, check_keys=False)

    def register_key(self, newkey):
        keysdoc = self.keyc.find_one()
        curkeys = keysdoc[self.kKEYS]
        if newkey in curkeys:
            return False
        curkeys.append(newkey)
        keysdoc[self.kKEYS] = curkeys
        self.keyc.save(keysdoc, safe=True)
        return True

    def ensure_keys(self, keys):
        keysdoc = self.keyc.find_one()
        curkeys = keysdoc[self.kKEYS]
        newkeys = set(keys) - set(curkeys)
        if newkeys:
            curkeys.extend(newkeys)
            keysdoc[self.kKEYS] = curkeys
            self.keyc.save(keysdoc, safe=True)

    def clear(self):
        self.conn.drop_database(self.db)
        self._bootstrap()

    def _add_log_record(self, record):
        self.logc.insert(record)
