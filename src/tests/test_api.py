from requests import Session
import unittest

from newrelic_logging import api, SalesforceApiException, LoginException
from . import \
    AuthenticatorStub, \
    ResponseStub, \
    SessionStub, \
    MultiRequestSessionStub


class TestApi(unittest.TestCase):
    def test_get_calls_session_get_with_url_access_token_and_default_stream_flag_and_invokes_cb_and_returns_result_on_200(self):
        '''
        get() makes a request with the given URL, access token, and default stream flag and invokes the callback with response and returns the result on a 200 status code
        given: an authenticator
        and given: a session
        and given: a url
        and given: a service URL
        and given: a callback
        when: get() is called
        then: session.get() is called with full URL, access token, and default stream flag
        and when: response status code is 200
        then: invokes callback with response and returns result
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
        )
        response = ResponseStub(200, 'OK', 'OK', [])
        session = SessionStub()
        session.response = response

        def cb(response):
            return response.text

        # execute
        val = api.get(auth, session, '/foo', cb)

        # verify
        self.assertEqual(session.url, 'https://my.salesforce.test/foo')
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertFalse(session.stream)
        self.assertIsNotNone(val)
        self.assertEqual(val, 'OK')

    def test_get_calls_session_get_with_url_access_token_and_given_stream_flag_and_invokes_cb_and_returns_result_on_200(self):
        '''
        get() makes a request with the given URL, access token, and stream flag and invokes the callback with response and returns the result on a 200 status code
        given: an authenticator
        and given: a session
        and given: a url
        and given: a callback
        when: get() is called
        then: session.get() is called with full URL, access token, and stream flag
        and when: response status code is 200
        then: invokes callback with response and returns result
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
        )
        response = ResponseStub(200, 'OK', 'OK', [])
        session = SessionStub()
        session.response = response

        def cb(response):
            return response.text

        # execute
        val = api.get(auth, session, '/foo', cb, stream=True)

        # verify
        self.assertEqual(session.url, 'https://my.salesforce.test/foo')
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertTrue(session.stream)
        self.assertIsNotNone(val)
        self.assertEqual(val, 'OK')

    def test_get_raises_on_response_not_200_or_401(self):
        '''
        get() raises a SalesforceApiException when the response status code is not 200 or 401
        given: an authenticator
        and given: a session
        and given: a service url
        and given: a callback
        when: get() is called
        then: session.get() is called with full URL, access token, and default stream flag
        and when: response status code is not 200
        and when: response status code is not 401
        then: raises a SalesforceApiException
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
        )
        response = ResponseStub(500, 'Server Error', 'Server Error', [])
        session = SessionStub()
        session.response = response

        def cb(response):
            return response

        # execute / verify
        with self.assertRaises(SalesforceApiException) as _:
            _ = api.get(
                auth,
                session,
                '/foo',
                cb,
            )

        self.assertEqual(session.url, 'https://my.salesforce.test/foo')
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertFalse(session.stream)

    def test_get_raises_on_connection_error(self):
        '''
        get() raises a SalesforceApiException when session.get() raises a ConnectionError
        given: an authenticator
        and given: a session
        and given: a service url
        and given: a callback
        when: get() is called
        then: session.get() is called with full URL, access token, and default stream flag
        and when: session.get() raises a ConnectionError
        then: raises a SalesforceApiException
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
        )
        response = ResponseStub(500, 'Server Error', 'Server Error', [])
        session = SessionStub(raise_connection_error=True)
        session.response = response

        def cb(response):
            return response

        # execute / verify
        with self.assertRaises(SalesforceApiException) as _:
            _ = api.get(
                auth,
                session,
                '/foo',
                cb,
            )

        self.assertEqual(session.url, 'https://my.salesforce.test/foo')
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertFalse(session.stream)

    def test_get_raises_on_request_exception(self):
        '''
        get() raises a SalesforceApiException when session.get() raises a RequestException
        given: an authenticator
        and given: a session
        and given: a service url
        and given: a callback
        when: get() is called
        then: session.get() is called with full URL, access token, and default stream flag
        and when: session.get() raises a RequestException
        then: raises a SalesforceApiException
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
        )
        response = ResponseStub(500, 'Server Error', 'Server Error', [])
        session = SessionStub(raise_error=True)
        session.response = response

        def cb(response):
            return response

        # execute / verify
        with self.assertRaises(SalesforceApiException) as _:
            _ = api.get(
                auth,
                session,
                '/foo',
                cb,
            )

        self.assertEqual(session.url, 'https://my.salesforce.test/foo')
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertFalse(session.stream)

    def test_get_raises_login_exception_if_reauthenticate_does(self):
        '''
        get() raises a LoginException when the status code is 401 and reauthenticate() raises a LoginException
        given: an authenticator
        and given: a session
        and given: a service url
        and given: a callback
        when: get() is called
        then: session.get() is called with full URL, access token, and default stream flag
        and when: response status code is 401
        then: reauthenticate() is called
        and when: reauthenticate() raises a LoginException
        then: raises a LoginException
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
            raise_login_error=True
        )
        response = ResponseStub(401, 'Unauthorized', 'Unauthorized', [])
        session = SessionStub()
        session.response = response

        def cb(response):
            return response

        # execute / verify
        with self.assertRaises(LoginException) as _:
            _ = api.get(
                auth,
                session,
                '/foo',
                cb,
            )

        self.assertEqual(session.url, 'https://my.salesforce.test/foo')
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertFalse(session.stream)
        self.assertTrue(auth.reauthenticate_called)

    def test_get_calls_reauthenticate_on_401_and_invokes_cb_with_response_on_200(self):
        '''
        get() calls reauthenticate() on a 401 and then invokes the callback with response and returns the result on a 200 status code
        given: an authenticator
        and given: a session
        and given: a service url
        and given: a callback
        when: get() is called
        then: session.get() is called with given URL, access token, and default stream flag
        and when: response status code is 401
        then: reauthenticate() is called
        and when: reauthenticate() does not throw a LoginException
        then: request is executed again with the same URL and stream setting as the first call to session.get() and the second access token
        and when: it returns a 200
        then: calls callback with response and returns result
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
            access_token_2='567890',
        )
        response1 = ResponseStub(401, 'Unauthorized', 'Unauthorized', [])
        response2 = ResponseStub(200, 'OK', 'OK', [])
        session = MultiRequestSessionStub(responses=[response1, response2])

        def cb(response):
            return response.text

        # execute
        val = api.get(auth, session, '/foo', cb)

        # verify
        self.assertEqual(len(session.requests), 2)
        self.assertEqual(
            session.requests[0]['url'],
            'https://my.salesforce.test/foo',
        )
        self.assertTrue('Authorization' in session.requests[0]['headers'])
        self.assertEqual(
            session.requests[0]['headers']['Authorization'],
            'Bearer 123456',
        )
        self.assertEqual(
            session.requests[0]['stream'],
            False,
        )
        self.assertTrue(auth.reauthenticate_called)
        self.assertEqual(
            session.requests[1]['url'],
            'https://my.salesforce.test/foo',
        )
        self.assertTrue('Authorization' in session.requests[1]['headers'])
        self.assertEqual(
            session.requests[1]['headers']['Authorization'],
            'Bearer 567890',
        )
        self.assertEqual(
            session.requests[1]['stream'],
            False,
        )
        self.assertIsNotNone(val)
        self.assertEqual(val, 'OK')

    def test_get_passed_correct_params_after_reauthenticate(self):
        '''
        get() receives the correct set of parameters when it is called after reauthenticate() succeeds
        given: an authenticator
        and given: a session
        and given: a service url
        and given: a callback
        when: get() is called
        then: session.get() is called with full URL, access token, and default stream flag
        and when: response status code is 401
        then: reauthenticate() is called
        and when: reauthenticate() does not throw a LoginException
        then: request is executed again with the same URL and stream setting as the first call to session.get() and the second access token
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
            access_token_2='567890'
        )
        response1 = ResponseStub(401, 'Unauthorized', 'Unauthorized', [])
        response2 = ResponseStub(200, 'OK', 'OK', [])
        session = MultiRequestSessionStub(responses=[response1, response2])

        def cb(response):
            return response.text

        # execute
        val = api.get(auth, session, '/foo', cb, stream=True)

        # verify
        self.assertEqual(len(session.requests), 2)
        self.assertTrue(auth.reauthenticate_called)
        self.assertEqual(
            session.requests[0]['url'],
            'https://my.salesforce.test/foo',
        )
        self.assertTrue('Authorization' in session.requests[0]['headers'])
        self.assertEqual(
            session.requests[0]['headers']['Authorization'],
            'Bearer 123456',
        )
        self.assertEqual(
            session.requests[0]['stream'],
            True,
        )
        self.assertEqual(
            session.requests[1]['url'],
            'https://my.salesforce.test/foo',
        )
        self.assertTrue('Authorization' in session.requests[1]['headers'])
        self.assertEqual(
            session.requests[1]['headers']['Authorization'],
            'Bearer 567890',
        )
        self.assertEqual(
            session.requests[1]['stream'],
            True,
        )
        self.assertIsNotNone(val)
        self.assertEqual(val, 'OK')

    def test_get_calls_reauthenticate_on_401_and_raises_on_non_200(self):
        '''
        get() function calls reauthenticate() on a 401 and then throws a SalesforceApiException on a non-200 status code
        given: an authenticator
        and given: a session
        and given: a service url
        and given: a callback
        when: get() is called
        then: session.get() is called with full URL, access token, and default stream flag
        and when: response status code is 401
        then: reauthenticate() is called
        and when: reauthenticate() does not throw a LoginException
        then: request is executed again with the same URL and stream setting as the first call to session.get() and the second access token
        and when: it returns a non-200 status code
        then: throws a SalesforceApiException
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
            access_token_2='567890',
        )
        response1 = ResponseStub(401, 'Unauthorized', 'Unauthorized', [])
        response2 = ResponseStub(401, 'Unauthorized', 'Unauthorized 2', [])
        session = MultiRequestSessionStub(responses=[response1, response2])

        def cb(response):
            return response

        # execute / verify
        with self.assertRaises(SalesforceApiException) as _:
            _ = api.get(
                auth,
                session,
                '/foo',
                cb,
            )

        self.assertEqual(len(session.requests), 2)
        self.assertTrue(auth.reauthenticate_called)
        self.assertEqual(
            session.requests[0]['url'],
            'https://my.salesforce.test/foo',
        )
        self.assertTrue('Authorization' in session.requests[0]['headers'])
        self.assertEqual(
            session.requests[0]['headers']['Authorization'],
            'Bearer 123456',
        )
        self.assertEqual(
            session.requests[0]['stream'],
            False,
        )
        self.assertEqual(
            session.requests[1]['url'],
            'https://my.salesforce.test/foo',
        )
        self.assertTrue('Authorization' in session.requests[1]['headers'])
        self.assertEqual(
            session.requests[1]['headers']['Authorization'],
            'Bearer 567890',
        )
        self.assertEqual(
            session.requests[1]['stream'],
            False,
        )

    def test_stream_lines_sets_fallback_encoding_and_calls_iter_lines_with_chunk_size_and_decode_unicode(self):
        '''
        stream_lines() sets a default encoding on the response and calls iter_lines with the given chunk size and the decode_unicode flag = True
        given: a response
        and given: a chunk size
        when: encoding on response is None
        then: fallback utf-8 is used and iter_lines is called with given chunk size and decode_unicode flag = True
        '''

        # setup
        response = ResponseStub(200, 'OK', 'OK', ['foo lines', 'bar line'])

        # execute
        lines = api.stream_lines(response, 1024)

        # verify
        next(lines)
        next(lines)
        # NOTE: this has to be done _after_ the generator iterator is called at
        # least once since the generator function is not run until the first
        # call to next()
        self.assertEqual(response.encoding, 'utf-8')
        self.assertEqual(response.chunk_size, 1024)
        self.assertTrue(response.decode_unicode)
        self.assertTrue(response.iter_lines_called)

    def test_stream_lines_uses_default_encoding_and_calls_iter_lines_with_chunk_size_and_decode_unicode(self):
        '''
        stream_lines() sets a default encoding on the response and calls iter_lines with the given chunk size and the decode_unicode flag = True
        given: a response
        and given: a chunk size
        when: encoding on response is set
        then: response encoding is used and iter_lines is called with given chunk size and decode_unicode flag = True
        '''

        # setup
        response = ResponseStub(
            200,
            'OK',
            'OK',
            ['foo lines', 'bar line'],
            encoding='iso-8859-1',
        )

        # execute
        lines = api.stream_lines(response, 1024)

        # verify
        next(lines)
        next(lines)
        # NOTE: this has to be done _after_ the generator iterator is called at
        # least once since the generator function is not run until the first
        # call to next()
        self.assertEqual(response.encoding, 'iso-8859-1')
        self.assertEqual(response.chunk_size, 1024)
        self.assertTrue(response.decode_unicode)
        self.assertTrue(response.iter_lines_called)

    def test_authenticate_calls_authenticator_authenticate(self):
        '''
        authenticate() calls authenticate() on the backing authenticator
        given: an authenticator
        and given: an api version
        and given: a session
        when: authenticate() is called
        then: authenticator.authenticate() is called
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
        )
        session = SessionStub()

        # execute
        sf_api = api.Api(auth, '55.0')
        sf_api.authenticate(session)

        # verify
        self.assertTrue(auth.authenticate_called)

    def test_authenticate_raises_login_exception_if_authenticator_authenticate_does(self):
        '''
        authenticate() calls authenticate() on the backing authenticator and raises a LoginException if authenticate() does
        given: an authenticator
        and given: an api version
        and given: a session
        when: authenticate() is called
        then: authenticator.authenticate() is called
        and when: authenticator.authenticate() raises a LoginException
        then: authenticate() raises a LoginException
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
            raise_login_error=True,
        )
        session = SessionStub()

        # execute / verify
        with self.assertRaises(LoginException) as _:
            sf_api = api.Api(auth, '55.0')
            sf_api.authenticate(session)

        self.assertTrue(auth.authenticate_called)

    def test_query_requests_correct_url_with_access_token_and_returns_json_response_on_success(self):
        '''
        query() calls the correct query API url with the access token and returns a JSON response when no errors occur
        given: an authenticator
        and given: an api version
        and given: a session
        and given: a query
        when: query() is called
        then: session.get() is called with correct URL and access token
        and: stream is set to False
        and when: session.get() response status code is 200
        then: calls callback with response and returns a JSON response
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
        )
        session = SessionStub()
        session.response = ResponseStub(200, 'OK', '{"foo": "bar"}', [] )

        # execute
        sf_api = api.Api(auth, '55.0')
        resp = sf_api.query(
            session,
            'SELECT+LogFile+FROM+EventLogFile',
        )

        # verify

        self.assertEqual(
            session.url,
            f'https://my.salesforce.test/services/data/v55.0/query?q=SELECT+LogFile+FROM+EventLogFile',
        )
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertFalse(session.stream)
        self.assertIsNotNone(resp)
        self.assertTrue(type(resp) is dict)
        self.assertTrue('foo' in resp)
        self.assertEqual(resp['foo'], 'bar')

    def test_query_requests_correct_url_with_access_token_given_api_version_and_returns_json_response_on_success(self):
        '''
        query() calls the correct query API url with the access token when a specific api version is given and returns a JSON response
        given: an authenticator
        and given: an api version
        and given: a session
        and given: a query
        when: query() is called
        and when: the api version parameter is specified
        then: session.get() is called with correct URL and access token
        and: stream is set to False
        and when: response status code is 200
        then: calls callback with response and returns a JSON response
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
        )
        session = SessionStub()
        session.response = ResponseStub(200, 'OK', '{"foo": "bar"}', [] )

        # execute
        sf_api = api.Api(auth, '55.0')
        resp = sf_api.query(
            session,
            'SELECT+LogFile+FROM+EventLogFile',
            '52.0',
        )

        # verify

        self.assertEqual(
            session.url,
            f'https://my.salesforce.test/services/data/v52.0/query?q=SELECT+LogFile+FROM+EventLogFile',
        )
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertFalse(session.stream)
        self.assertIsNotNone(resp)
        self.assertTrue(type(resp) is dict)
        self.assertTrue('foo' in resp)
        self.assertEqual(resp['foo'], 'bar')

    def test_query_raises_login_exception_if_get_does(self):
        '''
        query() calls the correct query API url with the access token and raises LoginException if get does
        given: an authenticator
        and given: an api version
        and given: a session
        and given: a query
        when: query() is called
        then: session.get() is called with correct URL and access token
        and: stream is set to False
        and when: session.get() raises a LoginException
        then: query() raises a LoginException
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
            raise_login_error=True
        )
        session = SessionStub()
        session.response = ResponseStub(401, 'Unauthorized', '{"foo": "bar"}', [] )

        # execute / verify
        with self.assertRaises(LoginException) as _:
            sf_api = api.Api(auth, '55.0')
            _ = sf_api.query(
                session,
                'SELECT+LogFile+FROM+EventLogFile',
            )

        self.assertEqual(
            session.url,
            f'https://my.salesforce.test/services/data/v55.0/query?q=SELECT+LogFile+FROM+EventLogFile',
        )
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertFalse(session.stream)

    def test_query_raises_salesforce_exception_if_get_does(self):
        '''
        query() calls the correct query API url with the access token and raises SalesforceApiException if get does
        given: an authenticator
        and given: an api version
        and given: a session
        and given: a query
        when: query() is called
        then: session.get() is called with correct URL and access token
        and: stream is set to False
        and when: session.get() raises a SalesforceApiException
        then: query() raises a SalesforceApiException
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
        )
        session = SessionStub()
        session.response = ResponseStub(500, 'ServerError', '{"foo": "bar"}', [] )

        # execute / verify
        with self.assertRaises(SalesforceApiException) as _:
            sf_api = api.Api(auth, '55.0')
            _ = sf_api.query(
                session,
                'SELECT+LogFile+FROM+EventLogFile',
            )

        self.assertEqual(
            session.url,
            f'https://my.salesforce.test/services/data/v55.0/query?q=SELECT+LogFile+FROM+EventLogFile',
        )
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertFalse(session.stream)

    def test_get_log_file_requests_correct_url_with_access_token_and_returns_generator_on_success(self):
        '''
        get_log_file() calls the correct url with the access token and returns a generator iterator
        given: an authenticator
        and given: an api version
        and given: a session
        and given: a log file path
        and given: a chunk size
        when: get_log_file() is called
        then: session.get() is called with correct URL and access token
        and: stream is set to True
        and when: response status code is 200
        and when: get() returns a response
        then: calls callback with response
        and: iter_lines is called with the correct chunk size
        and: returns a generator iterator
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
        )
        session = SessionStub()
        session.response = ResponseStub(
            200,
            'OK',
            '',
            [ 'COL1,COL2,COL3', 'foo,bar,baz' ],
        )

        # execute
        sf_api = api.Api(auth, '55.0')
        resp = sf_api.get_log_file(
            session,
            '/services/data/v52.0/sobjects/EventLogFile/00001111AAAABBBB/LogFile',
            chunk_size=8192,
        )

        # verify
        self.assertEqual(
            session.url,
            f'https://my.salesforce.test/services/data/v52.0/sobjects/EventLogFile/00001111AAAABBBB/LogFile',
        )
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertTrue(session.stream)
        self.assertIsNotNone(resp)
        line = next(resp)
        self.assertEqual('COL1,COL2,COL3', line)
        line = next(resp)
        self.assertEqual('foo,bar,baz', line)
        line = next(resp, None)
        self.assertIsNone(line)
        # NOTE: this has to be done _after_ the generator iterator is called at
        # least once since the generator function is not run until the first
        # call to next()
        self.assertTrue(session.response.iter_lines_called)
        self.assertEqual(session.response.chunk_size, 8192)

    def test_get_log_file_raises_login_exception_if_get_does(self):
        '''
        get_log_file() calls the correct query API url with the access token and raises a LoginException if get does
        given: an authenticator
        and given: an api version
        and given: a session
        and given: a log file path
        and given: a chunk size
        when: get_log_file() is called
        then: session.get() is called with correct URL and access token
        and: stream is set to True
        and when: get() raises a LoginException
        then: get_log_file() raises a LoginException
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
            raise_login_error=True,
        )
        session = SessionStub()
        session.response = ResponseStub(
            401,
            'Unauthorized',
            'Unauthorized',
            [ 'COL1,COL2,COL3', 'foo,bar,baz' ],
        )

        # execute / verify
        with self.assertRaises(LoginException) as _:
            sf_api = api.Api(auth, '55.0')
            _ = sf_api.get_log_file(
                session,
                '/services/data/v52.0/sobjects/EventLogFile/00001111AAAABBBB/LogFile',
                chunk_size=8192,
            )

        self.assertEqual(
            session.url,
            f'https://my.salesforce.test/services/data/v52.0/sobjects/EventLogFile/00001111AAAABBBB/LogFile',
        )
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertTrue(session.stream)

    def test_get_log_file_raises_salesforce_exception_if_get_does(self):
        '''
        get_log_file() calls the correct query API url with the access token and raises a SalesforceApiException if get does
        given: an authenticator
        and given: an api version
        and given: a session
        and given: a log file path
        and given: a chunk size
        when: get_log_file() is called
        then: session.get() is called with correct URL and access token
        and: stream is set to True
        and when: get() raises a SalesforceApiException
        then: get_log_file() raises a SalesforceApiException
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
        )
        session = SessionStub(raise_error=True)
        session.response = ResponseStub(
            200,
            'OK',
            '',
            [ 'COL1,COL2,COL3', 'foo,bar,baz' ],
        )

        # execute / verify
        with self.assertRaises(SalesforceApiException) as _:
            sf_api = api.Api(auth, '55.0')
            _ = sf_api.get_log_file(
                session,
                '/services/data/v52.0/sobjects/EventLogFile/00001111AAAABBBB/LogFile',
                chunk_size=8192,
            )

        self.assertEqual(
            session.url,
            f'https://my.salesforce.test/services/data/v52.0/sobjects/EventLogFile/00001111AAAABBBB/LogFile',
        )
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertTrue(session.stream)


class TestApiFactory(unittest.TestCase):
    def test_new_returns_api_with_correct_authenticator_and_version(self):
        '''
        new() returns a new Api instance with the given authenticator and version
        given: an authenticator
        and given: an api version
        when: new() is called
        then: returns a new Api instance with the given authenticator and version
        '''

        # setup
        auth = AuthenticatorStub(
            instance_url='https://my.salesforce.test',
            access_token='123456',
        )

        # execute
        api_factory = api.ApiFactory()
        sf_api = api_factory.new(auth, '55.0')

        # verify
        self.assertEqual(sf_api.authenticator, auth)
        self.assertEqual(sf_api.api_ver, '55.0')
