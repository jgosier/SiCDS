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

from itertools import imap
from operator import itemgetter
from pymongo import Connection
from pymongo.binary import Binary
from sicds.base import DocStore

class MongoStore(DocStore):
    #: the name of the collection that stores log entries
    cLOG = u'logentries'
    #: the name of the collection that stores api keys documents
    cKEYS = u'keys'
    #: the name of the collection that stores the dif documents
    cDIFS = u'difs'

    def __init__(self, url):
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
        self.difc = self.db[self.cDIFS]

    @staticmethod
    def _hash(key, difs):
        return Binary(DocStore._hash(key, difs))

    def _add_difs_records(self, records):
        # mongodb does not yet support bulk insert of docs with potentially
        # duplicate keys: http://jira.mongodb.org/browse/SERVER-509
        uniq = True
        for r in records:
            try:
                self.difc.insert(r, check_keys=False, safe=True)
            except:
                uniq = False
        return uniq

    def register_key(self, newkey):
        try:
            self.keyc.insert({self.kID: newkey}, check_keys=False, safe=True)
            return True
        except:
            return False

    def ensure_keys(self, keys):
        for key in keys:
            self.register_key(key)
        return imap(itemgetter(self.kID), self.keyc.find())

    def clear(self):
        self.conn.drop_database(self.db)
        self._bootstrap()

    def _add_log_record(self, record):
        self.logc.insert(record)

    def iterlog(self):
        return self.logc.find()
