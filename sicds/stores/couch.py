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
from operator import attrgetter, itemgetter
from base64 import urlsafe_b64encode
from sicds.base import DocStore

class CouchStore(DocStore):
    #: the key in api key documents that maps to the api key
    kAPIKEY = u'apikey'

    #: the id of the design doc specifying the view for api keys
    APIKEYS_DDOCID = u'apikeys'
    APIKEYS_VIEW_NAME = u'all'
    APIKEYS_VIEW_CODE = u'''
function (doc) {{
  if (doc.{0})
    emit(doc.{0}, null);
}}
'''.format(kAPIKEY)

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
        from couchdb import Server
        self.server = Server('http://{0}'.format(url.netloc))
        self.dbid = url.path.split('/')[1]
        self._bootstrap()

    def _bootstrap(self):
        if self.dbid not in self.server:
            self.server.create(self.dbid)
        self.db = self.server[self.dbid]
        from couchdb.design import ViewDefinition
        self.apikeys_view = ViewDefinition(self.APIKEYS_DDOCID,
            self.APIKEYS_VIEW_NAME, self.APIKEYS_VIEW_CODE)
        self.log_view = ViewDefinition(self.LOG_DDOCID,
            self.LOG_VIEW_NAME, self.LOG_VIEW_CODE)
        self.apikeys_view.sync(self.db)
        self.log_view.sync(self.db)

    @staticmethod
    def _hash(key, difs):
        return urlsafe_b64encode(DocStore._hash(key, difs))

    def _add_difs_records(self, records):
        results = self.db.update(records)
        return all(successful for (successful, id, rev_exc) in results)

    def register_key(self, newkey):
        if list(self.apikeys_view(self.db, key=newkey)):
            return False
        self.db.save({self.kAPIKEY: newkey})
        return True

    def ensure_keys(self, keys):
        for key in keys:
            self.register_key(key)
        return imap(itemgetter('key'), self.apikeys_view(self.db))

    def clear(self):
        if self.dbid in self.server:
            del self.server[self.dbid]
        self._bootstrap()

    def _add_log_record(self, record):
        self.db.save(record)

    def iterlog(self):
        return imap(attrgetter('doc'),
            self.log_view(self.db, include_docs=True))
