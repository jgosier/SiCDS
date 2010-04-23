from json import dumps
from pprint import pprint
from random import sample
from string import ascii_lowercase
from webtest import TestApp
import sys

from sicds.app import SiCDSApp
from sicds.config import SiCDSConfig

TESTKEY = 'sicds_test'
TESTPORT = 8635

def test_config(difstoreurl):
    return dict(port=TESTPORT, keys=[TESTKEY], difstore=difstoreurl)

# warning: test data stores will be cleared every time tests are run
# make sure these configs don't point to anything important!
test_configs = (
    test_config('tmp://'),
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
    def __init__(self, reqdata, res_status=200, res_body=''):
        self.req_body = dumps(reqdata)
        self.res_status = res_status
        self.res_body = res_body

    @property
    def expect_errors(self):
        return self.res_status >= 400

def result_str(uniq):
    return SiCDSApp.RES_UNIQ if uniq else SiCDSApp.RES_DUPE

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
res1_dupe = make_resp(req1, uniq=False)

tc_uniq = TestCase(req1, res_body=res1_uniq)
tc_dupe = TestCase(req1, res_body=res1_dupe)
test_cases.extend((tc_uniq, tc_dupe))

BADKEY = 'bad_key'
req_badkey = dict(req1, key=BADKEY)
tc_badkey = TestCase(req_badkey,
    res_status=SiCDSApp.X_UNRECOGNIZED_KEY().status_int,
    res_body=SiCDSApp.E_UNRECOGNIZED_KEY,
    )
test_cases.append(tc_badkey)

tc_missing_fields = TestCase({},
    res_status=SiCDSApp.X_BAD_REQ().status_int, 
    res_body=SiCDSApp.E_BAD_REQ,
    )
test_cases.append(tc_missing_fields)

req_extra_fields = dict(make_req(), extra='extra')
tc_extra_fields = TestCase(req_extra_fields,
    res_status=SiCDSApp.X_BAD_REQ().status_int, 
    res_body=SiCDSApp.E_BAD_REQ,
    )
test_cases.append(tc_extra_fields)


for config in test_configs:
    print('='*80)
    print('Testing difstore: {0}'.format(config['difstore']))
    print('-'*80)
    config = SiCDSConfig(config)
    config.difstore.clear()
    app = SiCDSApp(config.keys, config.difstore, config.logger)
    app = TestApp(app)
    for tc in test_cases:
        print('\nTesting request:')
        pprint(tc.req_body)
        resp = app.post('/', tc.req_body, status=tc.res_status,
            expect_errors=tc.expect_errors, headers={
            'content-type': 'application/json'})
        resp.mustcontain(tc.res_body)
