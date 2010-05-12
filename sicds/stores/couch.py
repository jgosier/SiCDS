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

from sicds.base import DocStore, StoreError

class CouchStore(DocStore):
    KEYDOCID = u'keys'
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
            self.db[self.KEYDOCID] = {self.kKEYS: []}
        from couchdb.design import ViewDefinition
        self._log_view = ViewDefinition(self.LOGDESIGNDOCID,
            self.LOG_VIEW_NAME, self.LOG_VIEW_CODE)
        self._log_view.sync(self.db)

    def _filter_old(self, ids):
        return [r.id for r in self.db.view('_all_docs', keys=ids)
                if r.id is not None]

    def _add_difs_records(self, records):
        results = self.db.update(records)
        failed = dict((id, exc) for (successful, id, exc)
                    in results if not successful)
        if failed:
            added = [id for (successful, id, _) in results if successful]
            raise StoreError({'added': added, 'failed': failed})

    def register_key(self, newkey):
        keydoc = self.db[self.KEYDOCID]
        currkeys = keydoc[self.kKEYS]
        if newkey in currkeys:
            return False
        currkeys.append(newkey)
        keydoc[self.kKEYS] = currkeys
        self.db[self.KEYDOCID] = keydoc
        return True

    def ensure_keys(self, keys):
        keysdoc = self.db[self.KEYDOCID]
        curkeys = keysdoc[self.kKEYS]
        newkeys = set(keys) - set(curkeys)
        if newkeys:
            curkeys.extend(newkeys)
            keysdoc[self.kKEYS] = curkeys
            successful, id, exc = self.db.update([keysdoc])[0]
            if not successful:
                raise StoreError({id: exc})
        return iter(curkeys)

    def clear(self):
        if self.dbid in self.server:
            del self.server[self.dbid]
        self._bootstrap()

    def _add_log_record(self, record):
        self.db.save(record)
