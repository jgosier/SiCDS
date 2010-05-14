#!/usr/bin/env python
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

from couchdb.http import ResourceConflict
from pymongo.errors import DuplicateKeyError
from sicds.app import Dif
from sicds.config import store_from_url
from unittest import TestCase, main

class TestThreadsafeCouch(TestCase):
    def setUp(self):
        self.couch = store_from_url('couchdb://localhost:5984/sicds_test')
        self.couch.clear()

    def test_insert_difs(self):
        '''
        Simulate the same client making two simultaneous requests checking
        for an item identified by either of two dif collections.
        '''
        couch = self.couch
        # couch inserts records in bulk
        def insert(records):
            return couch.db.update(records)
        key = u'key'
        dif1 = Dif(type='type1', value='value1')
        dif2 = Dif(type='type2', value='value2')
        hash1 = couch._hash(key, [dif1])
        hash2 = couch._hash(key, [dif2])
        record1 = couch._new_difs_record(hash1)
        record2 = couch._new_difs_record(hash2)
        # make two simultaneous requests to insert the records
        insert([record1, record2])
        insert([record1, record2])
        # bulk insert is not atomic, so both requests could end up with the
        # item identified as duplicate, but between the two of them, both
        # records should have gotten inserted
        self.assertTrue(record1[couch.kID] in couch.db)
        self.assertTrue(record2[couch.kID] in couch.db)

    def test_insert_key(self):
        '''
        Simulate the same client making two simultaneous requests to register
        the same key.
        '''
        couch = self.couch
        def insert(key):
            couch.keydb[key] = {}
        newkey = u'newkey'
        # request 1 tries to register newkey, succeeds
        insert(newkey)
        # request 2 tries to register newkey, fails
        self.assertRaises(ResourceConflict, lambda: insert(newkey))
        self.assertTrue(newkey in couch.keydb)

class TestThreadsafeMongo(TestCase):
    def setUp(self):
        self.mongo = store_from_url('mongodb://localhost:27017/sicds_test')
        self.mongo.clear()

    def test_insert_difs(self):
        '''
        Simulate the same client making two simultaneous requests checking
        for an item identified by either of two dif collections.
        '''
        mongo = self.mongo
        # currently mongo inserts records one at a time
        def insert(record):
            mongo.difc.insert(record, check_keys=False, safe=True)
        key = u'key'
        dif1 = Dif(type='type1', value='value1')
        dif2 = Dif(type='type2', value='value2')
        hash1 = mongo._hash(key, [dif1])
        hash2 = mongo._hash(key, [dif2])
        record1 = mongo._new_difs_record(hash1)
        record2 = mongo._new_difs_record(hash2)
        # let's say request 1 beats request 2 to inserting record1
        insert(record1)
        # request 2 causes error
        self.assertRaises(DuplicateKeyError, lambda: insert(record1))
        # Either request could beat the other to inserting record2.
        # If it's request 1, the item would be identified as unique for
        # request 1 and as duplicate for request 2.
        # If it's request 2, the item would be identified as duplicate to both
        # requests.
        insert(record2)
        # Either way, both records must have made it into the store:
        self.assertRaises(DuplicateKeyError, lambda: insert(record2))

    def test_insert_key(self):
        '''
        Simulate the same client making two simultaneous requests to register
        the same key.
        '''
        def insert(key):
            self.mongo.keyc.insert({self.mongo.kID: key}, check_keys=False, safe=True)
        newkey = u'newkey'
        insert(newkey)
        self.assertRaises(DuplicateKeyError, lambda: insert(newkey))


if __name__ == '__main__':
    main()
