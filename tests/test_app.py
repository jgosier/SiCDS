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

from functools import partial
from itertools import count
from json import dumps, loads
from pprint import pformat
from re import compile
from sys import stdout
from webob import exc
from webtest import TestApp

from sicds.app import SiCDSApp, IDRequest, IDResult, IDResponse, \
    KeyRegRequest, KeyRegResponse
from sicds.config import SiCDSConfig

TESTKEY = 'test_key'
TESTSUPERKEY = 'test_superkey'
TESTPORT = 8635

def test_config(store):
    return dict(port=TESTPORT, keys=[TESTKEY], superkey=TESTSUPERKEY,
        store=store, loggers=['store:'])

# test configs for all supported backends.
# comment out any that aren't installed on your system.
# warning: test data stores will be cleared every time tests are run
# make sure these configs don't point to anything important!
test_configs = (
    test_config('tmp:'),
    test_config('couchdb://localhost:5984/sicds_test'),
    test_config('mongodb://localhost:27017/sicds_test'),
    )

def next_str(prefix, counter):
    return '{0}{1}'.format(prefix, counter.next())

def make_req(key=TESTKEY, contentItems=[{}]):
    return IDRequest(key=key,
        contentItems=[make_item(**i) for i in contentItems]).unwrap

def make_item(id=None, difcollections=[{}], next_item=partial(next_str, 'item', count())):
    return dict(id=id or next_item(), difcollections=[make_coll(**c) for c in difcollections])

def make_coll(name=None, difs=[{}], next_coll=partial(next_str, 'collection', count())):
    return dict(name=name or next_coll(), difs=[make_dif(**d) for d in difs])

def make_dif(type=None, value=None,
        next_type=partial(next_str, 'type', count()),
        next_val=partial(next_str, 'value', count()),
        ):
    return dict(type=type or next_type(), value=value or next_val())

def make_resp(req, result='unique'):
    results = [IDResult(id=coll['id'], result=result)
        for coll in req['contentItems']]
    return IDResponse(key=req['key'], results=results).unwrap

class TestCase(object):
    '''
    Encapsulates a SiCDSRequest, a path, an expected response, and status code.
    '''
    def __init__(self, desc, req, resp='', path=SiCDSApp.R_IDENTIFY, status=200):
        self.desc = desc
        self.req = dumps(req) if isinstance(req, dict) else req
        self.resp = dumps(resp) if isinstance(resp, dict) else resp
        self.path = path
        self.status = status

    @property
    def expect_errors(self):
        return self.status >= 400

test_cases = []

# test that duplication identification works as expected
# first time we see an item it should be unique,
# subsequent times it should be duplicate
req1 = make_req()
res1_u = make_resp(req1, result='unique')
res1_d = make_resp(req1, result='duplicate')
tc_u = TestCase('item1 unique', req1, res1_u)
tc_d = TestCase('item1 now duplicate', req1, res1_d)
test_cases.extend((tc_u, tc_d))

# test multi-collection identification
# if we see an item with multiple collections, each of which we haven't seen
# before, it should be unique. if we see an item with multiple collections
# at least one of which we've seen before, it should be duplicate
c1 = make_coll()
c2 = make_coll()
c3 = make_coll()
i1 = make_item(difcollections=[c1, c2])
i2 = make_item(difcollections=[c2, c3])
i3 = make_item(difcollections=[c3])
req2 = make_req(contentItems=[i1])
req3 = make_req(contentItems=[i2])
req4 = make_req(contentItems=[i3])
res2_u = make_resp(req2, result='unique')
res3_d = make_resp(req3, result='duplicate')
res4_d = make_resp(req4, result='duplicate')
tc_u2 = TestCase('[c1, c2] collections unique', req2, res2_u)
tc_d2 = TestCase('[c2, c3] collections duplicate', req3, res3_d)
tc_d3 = TestCase('[c3] collection duplicate', req4, res4_d)
test_cases.extend((tc_u2, tc_d2, tc_d3))

# test that order of difs does not matter
d1 = make_dif()
d2 = make_dif()
c12 = make_coll(difs=[d1, d2])
c21 = make_coll(difs=[d2, d1])
i12 = make_item(difcollections=[c12])
i21 = make_item(difcollections=[c21])
req12 = make_req(contentItems=[i12])
req21 = make_req(contentItems=[i21])
res12_u = make_resp(req12, result='unique')
res21_d = make_resp(req21, result='duplicate')
tc_u12 = TestCase('[dif1, dif2] unique', req12, res12_u)
tc_d21 = TestCase('[dif2, dif1] duplicate (order does not matter)', req21, res21_d)
test_cases.extend((tc_u12, tc_d21))

# test registering a new key
NEWKEY = 'test_key2'
req_keyreg = KeyRegRequest(superkey=TESTSUPERKEY, newkey=NEWKEY).unwrap
res_keyreg = KeyRegResponse(key=NEWKEY, registered=True).unwrap
tc_keyreg = TestCase('register new key', req_keyreg, res_keyreg,
    path=SiCDSApp.R_REGISTER_KEY)
test_cases.append(tc_keyreg)

# existing content should look new to the client using the new key
req1_newkey = dict(req1, key=NEWKEY)
res1_newkey = dict(res1_u, key=NEWKEY)
tc_newkey_u = TestCase('item1 unique to new client', req1_newkey, res1_newkey)
test_cases.append(tc_newkey_u)

# check that various bad requests give error responses
req_badkey = dict(req1, key='bad_key')
tc_badkey = TestCase('reject bad key', req_badkey,
    status=exc.HTTPForbidden().status_int,
    )
test_cases.append(tc_badkey)

tc_missing_fields = TestCase('reject missing fields', {},
    status=exc.HTTPBadRequest().status_int,
    )
test_cases.append(tc_missing_fields)

req_extra_fields = dict(make_req(), extra='extra')
tc_extra_fields = TestCase('reject extra fields', req_extra_fields,
    status=exc.HTTPBadRequest().status_int,
    )
test_cases.append(tc_extra_fields)

req_too_large = {'too_large': ' '*SiCDSApp.REQMAXBYTES}
tc_too_large = TestCase('reject too large', req_too_large,
    status=exc.HTTPRequestEntityTooLarge().status_int,
    )
test_cases.append(tc_too_large)


npassed = nfailed = nerrors = 0
failures_per_config = []
for config in test_configs:
    config = SiCDSConfig(config)
    config.store.clear()
    store_type = config.store.__class__.__name__
    stdout.write('{0}:\t'.format(store_type))
    failures = []
    app = SiCDSApp(config.keys, config.superkey, config.store, config.loggers)
    app = TestApp(app)
    for tc in test_cases:
        try:
            resp = app.post(tc.path, tc.req, status=tc.status,
                expect_errors=tc.expect_errors, headers={
                'content-type': 'application/json'})
        except Exception as e:
            tc.got_resp = str(e)
            nerrors += 1
            failures.append(tc)
            stdout.write('E')
        else:
            if tc.status != resp.status_int or tc.resp not in resp:
                tc.got_resp = resp.body if tc.resp not in resp else \
                        '{0} != {1}'.format(tc.status, resp.status_int)
                nfailed += 1
                failures.append(tc)
                stdout.write('F')
            else:
                npassed += 1
                stdout.write('.')
        stdout.flush()
    stdout.write('\n')
    if failures:
        failures_per_config.append((store_type, failures))

print('\n{0} test(s) passed, {1} test(s) failed, {2} error(s).'.format(
    npassed, nfailed, nerrors))

whitespace = compile('\s+')
def indented(text, indent=' '*6, width=60, collapse_whitespace=True):
    if collapse_whitespace:
        text = ' '.join(whitespace.split(text))
    return '\n'.join((indent + text[i:i+width] for i in range(0, len(text), width)))

if nfailed:
    print('\nFailure summary:')
    for fs in failures_per_config:
        print('\n  For {0}:'.format(fs[0]))
        for tc in fs[1]:
            print('\n    test:')
            print('      {0}'.format(tc.desc))
            print('    request:')
            print(indented(tc.req, collapse_whitespace=False))
            print('    expected response:')
            print(indented(tc.resp))
            print('    got response:')
            print(indented(tc.got_resp))
