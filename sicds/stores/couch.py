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

from base64 import urlsafe_b64encode
from sicds.base import DocStore

class CouchStore(DocStore):
    LOGDESIGNDOCID = u'log'
    LOG_VIEW_NAME = u'entries'
    LOG_VIEW_CODE = u'''
function (doc) {{
  if (doc.{0})
    emit(doc.{0}, null);
}}
'''.format(DocStore.LOG_INDEX)

    def __init__(self, url):
        from couchdb import Server
        self.server = Server('http://{0}'.format(url.netloc))
        self.dbid = url.path.split('/')[1]
        self._bootstrap()

    def _bootstrap(self):
        fresh = self.dbid not in self.server
        if fresh:
            self.server.create(self.dbid)
        self.db = self.server[self.dbid]
        if fresh:
            self.db[self.KEYSDOCID] = {self.kKEYS: []}
        from couchdb.design import ViewDefinition
        self._log_view = ViewDefinition(self.LOGDESIGNDOCID,
            self.LOG_VIEW_NAME, self.LOG_VIEW_CODE)
        self._log_view.sync(self.db)

    @staticmethod
    def _hash(key, difs):
        return urlsafe_b64encode(DocStore._hash(key, difs))

    def _add_difs_records(self, records):
        results = self.db.update(records)
        return all(successful for (successful, id, rev_exc) in results)

    def register_key(self, newkey):
        keysdoc = self.db[self.KEYSDOCID]
        currkeys = keysdoc[self.kKEYS]
        if newkey in currkeys:
            return False
        currkeys.append(newkey)
        keysdoc[self.kKEYS] = currkeys
        self.db.save(keysdoc)
        return True

    def ensure_keys(self, keys):
        keysdoc = self.db[self.KEYSDOCID]
        curkeys = keysdoc[self.kKEYS]
        newkeys = set(keys) - set(curkeys)
        if newkeys:
            curkeys.extend(newkeys)
            keysdoc[self.kKEYS] = curkeys
            self.db.save(keysdoc)
        return iter(curkeys)

    def clear(self):
        if self.dbid in self.server:
            del self.server[self.dbid]
        self._bootstrap()

    def _add_log_record(self, record):
        self.db.save(record)
