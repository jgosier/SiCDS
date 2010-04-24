#!/usr/bin/env python

from json import dumps, loads
from pprint import pformat
from re import compile
from random import sample
from string import ascii_lowercase
from sys import stdout
from webtest import TestApp

from sicds.app import SiCDSApp
from sicds.config import SiCDSConfig

TESTKEY = 'sicds_test'
TESTPORT = 8635

def test_config(difstoreurl):
    return dict(port=TESTPORT, keys=[TESTKEY], difstore=difstoreurl, logger='null:')

# test configs for all supported backends.
# comment out any that aren't installed on your system.
# warning: test data stores will be cleared every time tests are run
# make sure these configs don't point to anything important!
test_configs = (
    test_config('tmp:'),
    test_config('couchdb://localhost:5984/sicds_test/difs'),
    test_config('mongodb://localhost:27017/sicds_test/difs'),
    )

def rand_str(chars=ascii_lowercase, length=7):
    return ''.join(sample(chars, length))

def make_req(key=TESTKEY, contentItems=[{}]):
    return dict(key=key, contentItems=[make_item(**i) for i in contentItems])

def make_item(id=None, difcollections=[{}]):
    return dict(id=id or rand_str(), difcollections=[make_coll(**c) for c in difcollections])

def make_coll(name=None, difs=[{}]):
    return dict(name=name or rand_str(), difs=[make_dif(**d) for d in difs])

def make_dif(type=None, value=None):
    return dict(type=type or rand_str(), value=value or rand_str())

class TestCase(object):
    '''
    Encapsulates a SiCDSRequest, an expected response status code, and part of
    an expected response body.

    Random data will be generated where ``reqdata`` lacks it.
    '''
    def __init__(self, reqdata, res_status_expect=200, res_body_expect=''):
        self.req_body = dumps(reqdata)
        self.res_status_expect = res_status_expect
        self.res_body_expect = res_body_expect

    @property
    def expect_errors(self):
        return self.res_status_expect >= 400

def result_str(uniq):
    return SiCDSApp.RES_UNIQ if uniq else SiCDSApp.RES_DUP

def make_resp(req, uniq=True):
    results = [dict(id=coll['id'], result=result_str(uniq))
        for coll in req['contentItems']]
    return dumps({'key': req['key'], 'results': results})

test_cases = []

# check that duplication identification works as expected
req1 = make_req()
res1_uniq = make_resp(req1, uniq=True)
res1_dup = make_resp(req1, uniq=False)

tc_uniq = TestCase(req1, res_body_expect=res1_uniq)
tc_dup = TestCase(req1, res_body_expect=res1_dup)
test_cases.extend((tc_uniq, tc_dup))

c1 = make_coll()
c2 = make_coll()
c3 = make_coll()
i1 = make_item(difcollections=[c1, c2])
i2 = make_item(difcollections=[c2, c3])
i3 = make_item(difcollections=[c3])
req2 = make_req(contentItems=[i1])
req3 = make_req(contentItems=[i2])
req4 = make_req(contentItems=[i3])
res2_uniq = make_resp(req2, uniq=True)
res3_dup = make_resp(req3, uniq=False)
res4_dup = make_resp(req4, uniq=False)
tc_uniq2 = TestCase(req2, res_body_expect=res2_uniq)
tc_dup2 = TestCase(req3, res_body_expect=res3_dup)
tc_dup3 = TestCase(req4, res_body_expect=res4_dup)
test_cases.extend((tc_uniq2, tc_dup2, tc_dup3))

# check that various bad requests give error responses
req_badkey = dict(req1, key='bad_key')
tc_badkey = TestCase(req_badkey,
    res_status_expect=SiCDSApp.X_UNRECOGNIZED_KEY().status_int,
    res_body_expect=SiCDSApp.E_UNRECOGNIZED_KEY,
    )
test_cases.append(tc_badkey)

tc_missing_fields = TestCase({},
    res_status_expect=SiCDSApp.X_BAD_REQ().status_int, 
    res_body_expect=SiCDSApp.E_BAD_REQ,
    )
test_cases.append(tc_missing_fields)

req_extra_fields = dict(make_req(), extra='extra')
tc_extra_fields = TestCase(req_extra_fields,
    res_status_expect=SiCDSApp.X_BAD_REQ().status_int, 
    res_body_expect=SiCDSApp.E_BAD_REQ,
    )
test_cases.append(tc_extra_fields)

req_too_large = {'too_large': ' '*SiCDSApp.REQMAXBYTES}
tc_too_large = TestCase(req_too_large,
    res_status_expect=SiCDSApp.X_REQ_TOO_LARGE().status_int, 
    res_body_expect=SiCDSApp.E_REQ_TOO_LARGE,
    )
test_cases.append(tc_too_large)


npassed = nfailed = 0
failures_per_config = []
for config in test_configs:
    config = SiCDSConfig(config)
    config.difstore.clear()
    difstore_type = config.difstore.__class__.__name__
    stdout.write('{0}:\t'.format(difstore_type))
    failures = []
    app = SiCDSApp(config.keys, config.difstore, config.logger)
    app = TestApp(app)
    for tc in test_cases:
        resp = app.post('/', tc.req_body, status=tc.res_status_expect,
            expect_errors=tc.expect_errors, headers={
            'content-type': 'application/json'})
        if tc.res_body_expect not in resp:
            tc.res_status_got = resp.status_int
            tc.res_body_got = resp.body
            nfailed += 1
            failures.append(tc)
            stdout.write('F')
        else:
            npassed += 1
            stdout.write('.')
        stdout.flush()
    stdout.write('\n')
    if failures:
        failures_per_config.append((difstore_type, failures))

print('\n{0} test(s) passed, {1} test(s) failed.'.format(npassed, nfailed))

whitespace = compile('\s+')
def indented(text, indent=' '*6, width=60, collapse_whitespace=True):
    if collapse_whitespace:
        text = ' '.join(whitespace.split(text))
    return '\n'.join((indent + text[i:i+width] for i in range(0, len(text), width)))

if failures_per_config:
    print('\nFailure summary:')
    for fs in failures_per_config:
        print('\n  For {0}:'.format(fs[0]))
        for tc in fs[1]:
            print('\n    request:')
            print(indented(tc.req_body, collapse_whitespace=False))
            print('    expected response:')
            print(indented(tc.res_body_expect))
            print('    got response:')
            print(indented(tc.res_body_got))
