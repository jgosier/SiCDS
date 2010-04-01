from webob import Request
from wsgiproxy.exactproxy import proxy_exact_request
from simplejson import loads, dumps
import sys

# XXX take config from command line and start local server ourselves
# (wiping out and creating test dbs as necessary)
# rather than expecting server to be running and dbs to be set up already
KEY = 'sicds_test'
if sys.argv[1:]:
    server = sys.argv[1]
else:
    server = 'http://localhost:8080'

def difdict(type, value):
    return {'type': type, 'value': value}

def contentdict(id, type_value_pairs):
    return {'id': id, 'difs': [difdict(t, v) for (t, v) in type_value_pairs]}

def resultsdict(id_result_pairs, key=KEY):
    return {'key': key, 'results': [
        {'id': id, 'result': result} for (id, result) in id_result_pairs]}

class TestCase(object):
    def __init__(self, data, expectstatus, expectbody=None, key=KEY):
        if isinstance(data, dict):
            self.data = dict(data, key=key)
        else:
            self.data = {'key': key, 'content': [
                contentdict(id, tvp) for (id, tvp) in data]}
        self.expectstatus = expectstatus
        self.expectbody = expectbody

data1 = (
    ('df7sdfsd0f8sdsdd8fsdfdsfs980',
       (('email_address', 'one@someaddress.com'),
        ('email_subject', 'the subject of email one'),
        ('email_abstract', 'The first X chars from email one'),
        )),
    ('duiwqoue87d8s7dwu89d8duedoe8',
       (('email_address', 'two@someaddress.com'),
        ('email_subject', 'the subject of email two'),
        ('email_abstract', 'The first X chars from email two'),
        )),
    )

data2 = (
    ('ysudy87d7a87sd6wdy78ed68ead',
       (('unique_tweet_id', 'the 1st twitter id of the source'),
        ('tweet_text', 'this would be the content of the tweet'),
        )),
    ('usidcyas7d6sa76fd5f6sd5f7s7',
       (('unique_tweet_id', 'the 2nd twitter id of the source'),
        ('tweet_text', 'this would be the content of the tweet'),
        )),
    )

TESTCASES = (
    TestCase(
        data1,
        200,
        expectbody=resultsdict(
            (('df7sdfsd0f8sdsdd8fsdfdsfs980', 'unique'),
             ('duiwqoue87d8s7dwu89d8duedoe8', 'unique'),
            ),
            )
        ),

    TestCase(
        data1,
        200,
        expectbody=resultsdict(
            (('df7sdfsd0f8sdsdd8fsdfdsfs980', 'duplicate'),
             ('duiwqoue87d8s7dwu89d8duedoe8', 'duplicate'),
            ),
            )
        ),

    TestCase(
        data2,
        200,
        expectbody=resultsdict(
            (('ysudy87d7a87sd6wdy78ed68ead', 'unique'),
             ('usidcyas7d6sa76fd5f6sd5f7s7', 'unique'),
            ),
            ),
        ),

    TestCase(
        {'content': [{'id': 'id1', 'difs': [{'type': 'foo', 'value': 'bar'}]}]},
        400,
        key='badkey'
        ),

    TestCase(
        {'content': [{'id': 'missing difs'}]},
        400,
        ),

    TestCase(
        {'content': [{'id': 'extra fields', 'difs': [{'type': 't', 'value': 'v', 'foo': 'f'}]}]},
        400,
        ),

    TestCase(
        {'content': [{'id': 'bad type', 'difs': False}]},
        400,
        ),

    )


def submit(data):
    req = Request.blank(server)
    req.method = 'POST'
    req.content_type = 'application/json'
    req.body = dumps(data)
    resp = req.get_response(proxy_exact_request)
    body = resp.body
    if resp.content_type == 'application/json':
        body = loads(body)
    return resp.status_int, body

def succeeded(status, body, expectstatus, expectbody=None):
    if status != expectstatus:
        return False
    if expectbody is not None and body != expectbody:
        return False
    return True

npassed = nfailed = 0
for t in TESTCASES:
    status, body = submit(t.data)
    if succeeded(status, body, t.expectstatus, t.expectbody):
        npassed += 1
        sys.stdout.write('.')
    else:
        nfailed += 1
        sys.stdout.write('F')
    sys.stdout.flush()

print('\n{0} test(s) passed, {1} test(s) failed'.format(npassed, nfailed))
