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

from couchdb import Server
from couchdb.design import ViewDefinition
from itertools import imap
from operator import attrgetter, itemgetter
from base64 import urlsafe_b64encode
from sicds.base import DocStore

class CouchStore(DocStore):
    #: the id of the design doc specifying the view for log records
    LOG_DDOCID = u'log'
    LOG_VIEW_NAME = u'by_{0}'.format(DocStore.LOG_INDEX)
    LOG_VIEW_CODE = u'''
function (doc) {{
  if (doc.{0})
    emit(doc.{0}, null);
}}
'''.format(DocStore.LOG_INDEX)

    def __init__(self, url):
        self.server = Server('http://{0}'.format(url.netloc))
        self.dbid = url.path.split('/')[1]
        self.keydbid = self.dbid + '_keys'
        self._bootstrap()

    def _bootstrap(self):
        if self.dbid not in self.server:
            self.server.create(self.dbid)
        if self.keydbid not in self.server:
            self.server.create(self.keydbid)
        self.db = self.server[self.dbid]
        self.keydb = self.server[self.keydbid]
        self.log_view = ViewDefinition(self.LOG_DDOCID,
            self.LOG_VIEW_NAME, self.LOG_VIEW_CODE)
        self.log_view.sync(self.db)

    @staticmethod
    def _hash(key, difs):
        return urlsafe_b64encode(DocStore._hash(key, difs))

    def _add_difs_records(self, records):
        results = self.db.update(records)
        return all(successful for (successful, id, rev_exc) in results)

    def register_key(self, newkey):
        try:
            self.keydb[newkey] = {}
        except:
            return False
        return True

    def ensure_keys(self, keys):
        for key in keys:
            self.register_key(key)
        return imap(attrgetter('id'), self.keydb.view('_all_docs'))

    def clear(self):
        if self.dbid in self.server:
            del self.server[self.dbid]
        if self.keydbid in self.server:
            del self.server[self.keydbid]
        self._bootstrap()

    def _add_log_record(self, record):
        self.db.save(record)

    def iterlog(self):
        return imap(attrgetter('doc'),
            self.log_view(self.db, include_docs=True))
