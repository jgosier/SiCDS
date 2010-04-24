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

# warning: test data stores will be cleared every time tests are run
# make sure these configs don't point to anything important!
test_configs = (
    test_config('tmp:'),
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
    if uniq in (True, False):
        # set all results to uniq
        results = [dict(id=coll['id'], result=result_str(uniq))
            for coll in req['contentItems']]
    else:
        # uniq is a mapping specifying results per id
        results = [dict(id=id, result=result_str(uniq))
            for (id, result) in uniq.iteritems()]

    return dumps({'key': req['key'], 'results': results})

test_cases = []

req1 = make_req()
res1_uniq = make_resp(req1)
res1_dup = make_resp(req1, uniq=False)

tc_uniq = TestCase(req1, res_body_expect=res1_uniq)
tc_dup = TestCase(req1, res_body_expect=res1_dup)
test_cases.extend((tc_uniq, tc_dup))

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
    failures = []
    app = SiCDSApp(config.keys, config.difstore, config.logger)
    app = TestApp(app)
    for tc in test_cases:
        stdout.write('.')
        stdout.flush()
        resp = app.post('/', tc.req_body, status=tc.res_status_expect,
            expect_errors=tc.expect_errors, headers={
            'content-type': 'application/json'})
        if tc.res_body_expect not in resp:
            tc.res_status_got = resp.status_int
            tc.res_body_got = resp.body
            nfailed += 1
            failures.append(tc)
        else:
            npassed += 1
    if failures:
        failures_per_config.append((difstore_type, failures))

print('\n{0} tests passed, {1} tests failed.'.format(npassed, nfailed))

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
