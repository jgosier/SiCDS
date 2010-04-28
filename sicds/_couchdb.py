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

from base import DocStore, NoSuchKey, UpdateFailed, serialize
from string import digits, ascii_letters

class CouchStore(DocStore):#, BaseLogger):
    DIFDESIGNDOCID = 'difs'
    KEYDOCID = 'keys'

    DIF_VIEW_NAME = 'difs_by_key'
    DIF_VIEW_CODE = '''
function (doc) {{
  if (doc.{0})
    emit(doc.{0}, null);
}}
'''.format(DocStore.kDIFS)

    def __init__(self, url):
        '''
        Base class for data stores backed by CouchDB. Opens a connection to
        the CouchDB database specified in ``url``.
        '''
        from couchdb import Server
        self.server = Server('http://{0}'.format(url.netloc))
        self.dbid = url.path.split('/')[1]
        if self.dbid not in self.server:
            self._bootstrap()

    def _bootstrap(self):
        self.server.create(self.dbid)
        self.db = self.server[self.dbid]
        self.db[self.KEYDOCID] = {self.kKEYS: []}
        from couchdb.design import ViewDefinition
        self._dif_view = ViewDefinition(self.DIFDESIGNDOCID,
            self.DIF_VIEW_NAME, self.DIF_VIEW_CODE)
        self._dif_view.sync(self.db)

    def has(self, key, difs):
        '''
        Returns True iff difs is in the database.
        '''
        s = serialize(key, difs)
        return bool(list(self._dif_view(self.db, key=s)))

    def add(self, key, difs):
        '''
        Adds a set of difs to the database.
        '''
        doc = self._as_doc(key, difs)
        # try generating a docid based on python hash value of contents
        docid = hash(doc[self.kDIFS])
        docid = change_base(docid) # use large base for shorter id
        try:
            if docid not in self.db:
                self.db[docid] = doc
            else:
                # let couch assign the id (will be much longer)
                self.db.save(doc)
        except Exception as e:
            raise UpdateFailed(str(e))

    def register_key(self, newkey):
        keydoc = self.db[self.KEYDOCID]
        currkeys = keydoc[self.kKEYS]
        if newkey in currkeys:
            return False
        currkeys.append(newkey)
        try:
            self.db[self.KEYDOCID] = keydoc
            return True
        except Exception as e:
            raise UpdateFailed(str(e))

    def ensure_keys(self, keys):
        keydoc = self.db[self.KEYDOCID]
        currkeys = keydoc[self.kKEYS]
        updated = False
        for key in keys:
            if key not in currkeys:
                currkeys.append(key)
                updated = True
        if updated:
            try:
                self.db[self.KEYDOCID] = keydoc
            except Exception as e:
                raise UpdateFailed(str(e))

    #def unregister(self, key):
    #    keydoc = self.db[self.KEYDOCID]
    #    currkeys = keydoc[self.kKEYS]
    #    try:
    #        currkeys.remove(key)
    #    except ValueError:
    #        raise NoSuchKey(key)
    #    else:
    #        try:
    #            self.db[self.KEYDOCID] = keydoc
    #        except Exception as e:
    #            raise UpdateFailed(str(e))

    def clear(self):
        if self.dbid in self.server:
            del self.server[self.dbid]
        self._bootstrap()


#class CouchLogger(CouchStore, BaseLogger):
#    '''
#    Stores log entries in a CouchDB instance.
#    '''
#    def _store(self, entry):
#        self.db.save(entry)

def change_base(x, charset=digits+ascii_letters, base=None):
    '''
    Returns ``x`` in base ``base`` using digits from ``charset``. With
    ``base=None`` base will be set to ``len(charset)`` resulting in the
    shortest possible string for the given charset.

    >>> max32 = 2**32 - 1
    >>> change_base(max32, base=16)
    'ffffffff'
    >>> change_base(max32)
    '4GFfc3'

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
