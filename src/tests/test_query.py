from datetime import datetime
import unittest

from newrelic_logging import SalesforceApiException
from newrelic_logging import config as mod_config, query, util
from . import \
    ResponseStub, \
    SessionStub

class TestQuery(unittest.TestCase):
    def test_get_returns_backing_config_value_when_key_exists(self):
        '''
        get() returns the value of the key in the backing config when the key exists
        given: a query string, a configuration, and an api version
        and given: a key
        when: get is called with the key
        then: returns value of the key from backing config
        '''

        # setup
        config = mod_config.Config({ 'foo': 'bar' })

        # execute
        q = query.Query(
            'SELECT+LogFile+FROM+EventLogFile',
            config,
            '55.0',
        )
        val = q.get('foo')

        # verify
        self.assertEqual(val, 'bar')

    def test_get_returns_backing_config_default_when_key_missing(self):
        '''
        get() returns the default value passed to the backing config.get when key does not exist in the backing config
        given: a query string, a configuration, and an api version
        when: get is called with a key and a default value
        and when: the key does not exist in the backing config
        then: returns default value passed to the backing config.get
        '''

        # setup
        config = mod_config.Config({})

        # execute
        q = query.Query(
            'SELECT+LogFile+FROM+EventLogFile',
            config,
            '55.0',
        )
        val = q.get('foo', 'beep')

        # verify
        self.assertEqual(val, 'beep')

    def test_execute_raises_exception_on_non_200_response(self):
        '''
        execute() raises exception on non-200 status code from Salesforce API
        given: a query string, a configuration, and an api version
        when: execute() is called with an http session, an instance url, and an access token
        and when: the response produces a non-200 status code
        then: raise a SalesforceApiException
        '''

        # setup
        config = mod_config.Config({})
        session = SessionStub()
        session.response = ResponseStub(500, 'Error', '', [])

        # execute/verify
        q = query.Query(
            'SELECT+LogFile+FROM+EventLogFile',
            config,
            '55.0',
        )

        with self.assertRaises(SalesforceApiException) as _:
            q.execute(session, 'https://my.salesforce.test', '123456')

    def test_execute_raises_exception_if_session_get_does(self):
        '''
        execute() raises exception if session.get() raises a RequestException
        given: a query string, a configuration, and an api version
        when: execute() is called with an http session, an instance url, and an access token
        and when: session.get() raises a RequestException
        then: raise a SalesforceApiException
        '''

        # setup
        config = mod_config.Config({})
        session = SessionStub(raise_error=True)
        session.response = ResponseStub(200, 'OK', '[]', [] )

        # execute/verify
        q = query.Query(
            'SELECT+LogFile+FROM+EventLogFile',
            config,
            '55.0',
        )

        with self.assertRaises(SalesforceApiException) as _:
            q.execute(session, 'https://my.salesforce.test', '123456')

    def test_execute_calls_query_api_url_with_token_and_returns_json_response(self):
        '''
        execute() calls the correct query API url with the access token and returns a json response
        given: a query string, a configuration, and an api version
        when: execute() is called with an http session, an instance url, and an access token
        then: a get request is made to the correct API url with the given access token and returns a json response
        '''

        # setup
        config = mod_config.Config({})
        session = SessionStub()
        session.response = ResponseStub(200, 'OK', '{"foo": "bar"}', [] )

        # execute
        q = query.Query(
            'SELECT+LogFile+FROM+EventLogFile',
            config,
            '55.0',
        )

        resp = q.execute(session, 'https://my.salesforce.test', '123456')

        # verify
        self.assertEqual(
            session.url,
            f'https://my.salesforce.test/services/data/v55.0/query?q=SELECT+LogFile+FROM+EventLogFile',
        )
        self.assertTrue('Authorization' in session.headers)
        self.assertEqual(session.headers['Authorization'], 'Bearer 123456')
        self.assertIsNotNone(resp)
        self.assertTrue(type(resp) is dict)
        self.assertTrue('foo' in resp)
        self.assertEqual(resp['foo'], 'bar')


class TestQueryFactory(unittest.TestCase):
    def test_build_args_creates_expected_dict(self):
        '''
        build_args() returns dictionary with expected properties
        given: a query factory
        when: build_args() is called with a time lag, timestamp, and generation interval
        then: returns dict with expected properties
        '''

        # setup
        _now = datetime.utcnow()

        def _utcnow():
            nonlocal _now
            return _now

        util._UTCNOW = _utcnow

        time_lag_minutes = 500
        last_to_timestamp = util.get_iso_date_with_offset(
            time_lag_minutes=time_lag_minutes * 2,
        )
        to_timestamp = util.get_iso_date_with_offset(
            time_lag_minutes=time_lag_minutes,
        )

        # execute
        f = query.QueryFactory()
        args = f.build_args(time_lag_minutes, last_to_timestamp, 'Daily')

        # verify
        self.assertIsNotNone(args)
        self.assertTrue(type(args) is dict)
        self.assertTrue('to_timestamp' in args)
        self.assertEqual(args['to_timestamp'], to_timestamp)
        self.assertTrue('from_timestamp' in args)
        self.assertEqual(args['from_timestamp'], last_to_timestamp)
        self.assertTrue('log_interval_type' in args)
        self.assertEqual(args['log_interval_type'], 'Daily')

    def test_get_env_returns_empty_dict_if_no_env(self):
        '''
        get_env() returns an empty dict if env is not in the passed query dict
        given: a query factory
        when: get_env() is called with a query dict
        and when: there is no env property in the query dict
        then: returns an empty dict
        '''

        # setup
        q = { 'query': 'SELECT LogFile FROM EventLogFile' }

        # execute
        f = query.QueryFactory()
        env = f.get_env(q)

        # verify
        self.assertIsNotNone(env)
        self.assertTrue(type(env) is dict)
        self.assertEqual(len(env), 0)

    def test_get_env_returns_empty_dict_if_env_not_dict(self):
        '''
        get_env() returns an empty dict if the passed query dict has an env property but it is not a dict
        given: a query factory
        when: get_env() is called with a query dict
        and when: there is an env property in the query dict
        and when: the env property is not a dict
        then: returns an empty dict
        '''

        # setup
        q = { 'query': 'SELECT LogFile FROM EventLogFile', 'env': 'foo' }

        # execute
        f = query.QueryFactory()
        env = f.get_env(q)

        # verify
        self.assertIsNotNone(env)
        self.assertTrue(type(env) is dict)
        self.assertEqual(len(env), 0)

    def test_get_env_returns_env_dict_from_query_dict(self):
        '''
        get_env() returns the env dict from the query dict when one is present
        given: a query factory
        when: get_env() is called with a query dict
        and when: there is an env property in the query dict
        and when: the env property is a dict
        then: returns the env dict
        '''

        # setup
        q = {
            'query': 'SELECT LogFile FROM EventLogFile',
            'env': { 'foo': 'bar' },
        }

        # execute
        f = query.QueryFactory()
        env = f.get_env(q)

        # verify
        self.assertIsNotNone(env)
        self.assertTrue(type(env) is dict)
        self.assertEqual(len(env), 1)
        self.assertTrue('foo' in env)
        self.assertEqual(env['foo'], 'bar')

    def test_new_returns_query_obj_with_encoded_query_with_args_replaced(self):
        '''
        new() returns a query instance with the given query with arguments replaced and URL encoded
        given: a query factory
        when: new() is called with a query dict, lag time, timestamp, generation interval, and default api version
        then: returns a query instance with the input query with arguments replaced and URL encoded
        '''

        # setup
        _now = datetime.utcnow()

        def _utcnow():
            nonlocal _now
            return _now

        util._UTCNOW = _utcnow

        to_timestamp = util.get_iso_date_with_offset(time_lag_minutes=500)
        last_to_timestamp = util.get_iso_date_with_offset(time_lag_minutes=1000)
        now = _now.isoformat(timespec='milliseconds') + "Z"
        env = { 'foo': 'now()' }

        # execute
        f = query.QueryFactory()
        q = f.new(
            {
                'query': 'SELECT LogFile FROM EventLogFile WHERE CreatedDate>={from_timestamp} AND CreatedDate<{to_timestamp} AND LogIntervalType={log_interval_type} AND Foo={foo}',
                'env': env,
            },
            500,
            last_to_timestamp,
            'Daily',
            '55.0',
        )

        # verify
        self.assertEqual(
            q.query,
            f'SELECT+LogFile+FROM+EventLogFile+WHERE+CreatedDate>={last_to_timestamp}+AND+CreatedDate<{to_timestamp}+AND+LogIntervalType=Daily+AND+Foo={now}'
        )

    def test_new_returns_query_obj_with_expected_config(self):
        '''
        new() returns a query instance with the input query dict minus the query property
        given: a query factory
        when: new() is called with a query dict, lag time, timestamp, generation interval, and default api version
        then: returns a query instance with a config equal to the input query dict minus the query property
        '''

        # setup
        last_to_timestamp = util.get_iso_date_with_offset(time_lag_minutes=1000)

        # execute
        f = query.QueryFactory()
        q = f.new(
            {
                'query': 'SELECT LogFile FROM EventLogFile',
                'foo': 'bar',
                'beep': 'boop',
                'bip': 0,
                'bop': 5,
            },
            500,
            last_to_timestamp,
            'Daily',
            '55.0',
        )

        # verify
        config = q.get_config()

        self.assertIsNotNone(config)
        self.assertTrue(type(config) is mod_config.Config)
        self.assertFalse('query' in config)
        self.assertTrue('foo' in config)
        self.assertEqual(config['foo'], 'bar')
        self.assertTrue('beep' in config)
        self.assertEqual(config['beep'], 'boop')
        self.assertTrue('bip' in config)
        self.assertEqual(config['bip'], 0)
        self.assertTrue('bop' in config)
        self.assertEqual(config['bop'], 5)

    def test_new_returns_query_obj_with_given_api_ver(self):
        '''
        new() returns a query instance with the api version specified in the query dict
        given: a query factory
        when: new() is called with a query dict, lag time, timestamp, generation interval, and default api version
        then: returns a query instance with the api version specified in the query dict
        '''

        # setup
        last_to_timestamp = util.get_iso_date_with_offset(time_lag_minutes=1000)

        # execute
        f = query.QueryFactory()
        q = f.new(
            {
                'query': 'SELECT LogFile FROM EventLogFile',
                'api_ver': '58.0'
            },
            500,
            last_to_timestamp,
            'Daily',
            '53.0',
        )

        # verify
        self.assertEqual(q.api_ver, '58.0')

    def test_new_returns_query_obj_with_default_api_ver(self):
        '''
        new() returns a query instance with the default api version specified on the new() call
        given: a query factory
        when: new() is called with a query dict, lag time, timestamp, generation interval, and default api version
        then: returns a query instance with the default api version specified on the the new() call
        '''

        # setup
        last_to_timestamp = util.get_iso_date_with_offset(time_lag_minutes=1000)

        # execute
        f = query.QueryFactory()
        q = f.new(
            {
                'query': 'SELECT LogFile FROM EventLogFile',
            },
            500,
            last_to_timestamp,
            'Daily',
            '53.0',
        )

        # verify
        self.assertEqual(q.api_ver, '53.0')
