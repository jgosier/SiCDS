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

from sicds.base import BaseLogger, DocStore, hash, serialize
from string import digits, ascii_letters

class CouchStore(DocStore):
    DIFDESIGNDOCID = u'difs'
    LOGDESIGNDOCID = u'log'
    KEYDOCID = u'keys'

    DIF_VIEW_NAME = u'difs_by_key'
    DIF_VIEW_CODE = u'''
function (doc) {{
  if (doc.{0})
    emit(doc.{0}, null);
}}
'''.format(DocStore.kDIFS)

    LOG_VIEW_NAME = u'entries'
    LOG_VIEW_CODE = u'''
function (doc) {{
  if (doc.{0})
    emit(doc.{0}, null);
}}
'''.format(BaseLogger.LOG_INDEX)

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
        self._dif_view = ViewDefinition(self.DIFDESIGNDOCID,
            self.DIF_VIEW_NAME, self.DIF_VIEW_CODE)
        self._log_view = ViewDefinition(self.LOGDESIGNDOCID,
            self.LOG_VIEW_NAME, self.LOG_VIEW_CODE)
        self._dif_view.sync(self.db)
        self._log_view.sync(self.db)

    def check(self, key, difs):
        s = self._serialize(key, difs)
        if list(self._dif_view(self.db, key=s)):
            return False
        doc = self._as_doc(key, difs)
        # try generating a docid based on hash value of contents
        docid = hash(key, difs) # sha1 hex digest
        docid = change_base(int(docid, 16)) # use large base for shorter id
        if docid not in self.db:
            self.db[docid] = doc
        else:
            # let couch assign the id, will be much longer
            self.db.save(doc)
        return True

    def register_key(self, newkey):
        keydoc = self.db[self.KEYDOCID]
        currkeys = keydoc[self.kKEYS]
        if newkey in currkeys:
            return False
        currkeys.append(newkey)
        self.db[self.KEYDOCID] = keydoc
        return True

    def ensure_keys(self, keys):
        keydoc = self.db[self.KEYDOCID]
        currkeys = keydoc[self.kKEYS]
        updated = False
        for key in keys:
            if key not in currkeys:
                currkeys.append(key)
                updated = True
        if updated:
            self.db[self.KEYDOCID] = keydoc

    def clear(self):
        if self.dbid in self.server:
            del self.server[self.dbid]
        self._bootstrap()

    def _append_log(self, entry):
        self.db.save(entry)

def change_base(x, charset=digits+ascii_letters, base=None):
    '''
    Returns ``x`` in base ``base`` using digits from ``charset``. With
    ``base=None`` base will be set to ``len(charset)`` resulting in the
    shortest possible string for the given charset.

    >>> uint32max = 2**32 - 1
    >>> as_hex = change_base(uint32max, base=16)
    >>> as_hex == hex(uint32max).lstrip('0x')
    True
    >>> len(change_base(uint32max, base=60)) < len(as_hex)
    True

    '''
    if x == 0:
        return '0'
    sign = -1 if x < 0 else 1
    x *= sign
    digits = []
    if base is None:
        base = len(charset)
    else:
        charset = charset[:base]
    while x:
        digits.append(charset[x % base])
        x /= base
    if sign < 0:
        digits.append('-')
    digits.reverse()
    return ''.join(digits)

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
