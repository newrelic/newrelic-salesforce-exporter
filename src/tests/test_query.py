from datetime import datetime
import unittest

from newrelic_logging import LoginException, SalesforceApiException
from newrelic_logging import config as mod_config, util, query
from . import \
    ApiStub, \
    SessionStub

class TestQuery(unittest.TestCase):
    def test_get_returns_backing_config_value_when_key_exists(self):
        '''
        get() returns the value of the key in the backing config when the key exists
        given: an api instance
        and given: a query string
        and given: a configuration
        and given: a key
        when: get() is called with the key
        then: return value of the key from backing config
        '''

        # setup
        api = ApiStub()
        config = mod_config.Config({ 'foo': 'bar' })

        # execute
        q = query.Query(
            api,
            'SELECT+LogFile+FROM+EventLogFile',
            config,
        )
        val = q.get('foo')

        # verify
        self.assertEqual(val, 'bar')

    def test_get_returns_backing_config_default_when_key_missing(self):
        '''
        get() returns the default value passed to the backing config.get when key does not exist in the backing config
        given: an api instance
        and given: a query string
        and given: a configuration
        and given: a key
        when: get() is called with a key and a default value
        and when: the key does not exist in the backing config
        then: returns default value passed to the backing config.get
        '''

        # setup
        api = ApiStub()
        config = mod_config.Config({})

        # execute
        q = query.Query(
            api,
            'SELECT+LogFile+FROM+EventLogFile',
            config,
        )
        val = q.get('foo', 'beep')

        # verify
        self.assertEqual(val, 'beep')

    def test_execute_raises_login_exception_if_api_query_does(self):
        '''
        execute() raises a LoginException if api.query() raises a LoginException
        given: an api instance
        and given: a query string
        and given: a configuration
        and given: an http session
        when: execute() is called with an http session
        then: calls api.query() with the given session, query string, and no api version
        and when: api.query() raises a LoginException (as a result of a reauthenticate)
        then: raise a LoginException
        '''

        # setup
        api = ApiStub(raise_login_error=True)
        config = mod_config.Config({})
        session = SessionStub()

        # execute/verify
        q = query.Query(
            api,
            'SELECT+LogFile+FROM+EventLogFile',
            config,
        )

        with self.assertRaises(LoginException) as _:
            q.execute(session)

    def test_execute_raises_salesforce_api_exception_if_api_query_does(self):
        '''
        execute() raises a SalesforceApiException if api.query() raises a SalesforceApiException
        given: an api instance
        and given: a query string
        and given: a configuration
        and given: an http session
        when: execute() is called with an http session
        then: calls api.query() with the given session, query string, and no api version
        and when: api.query() raises a SalesforceApiException
        then: raise a SalesforceApiException
        '''

        # setup
        api = ApiStub(raise_error=True)
        config = mod_config.Config({})
        session = SessionStub()

        # execute/verify
        q = query.Query(
            api,
            'SELECT+LogFile+FROM+EventLogFile',
            config,
        )

        with self.assertRaises(SalesforceApiException) as _:
            q.execute(session)

    def test_execute_calls_query_api_with_query_and_returns_result(self):
        '''
        execute() calls api.query() with the given session, query string, and no api version and returns the result
        given: an api instance
        and given: a query string
        and given: a configuration
        and given: an http session
        when: execute() is called
        then: calls api.query() with the given session, query string, and no api version
        and: return query result
        '''

        # setup
        api = ApiStub(query_result={ 'foo': 'bar' })
        config = mod_config.Config({})
        session = SessionStub()

        # execute
        q = query.Query(
            api,
            'SELECT+LogFile+FROM+EventLogFile',
            config,
        )

        resp = q.execute(session)

        # verify
        self.assertEqual('SELECT+LogFile+FROM+EventLogFile', api.soql)
        self.assertIsNone(api.query_api_ver)
        self.assertIsNotNone(resp)
        self.assertTrue(type(resp) is dict)
        self.assertTrue('foo' in resp)
        self.assertEqual(resp['foo'], 'bar')

    def test_execute_calls_query_api_with_query_and_api_ver_and_returns_result(self):
        '''
        execute() calls api.query() with the given session, query string, and api version and returns the result
        given: an api instance
        and given: a query string
        and given: a configuration
        and given: an api version
        and given: an http session
        when: execute() is called
        then: calls api.query() with the given session, query string, and api version
        and: return query result
        '''

        # setup
        api = ApiStub(query_result={ 'foo': 'bar' })
        config = mod_config.Config({})
        session = SessionStub()

        # execute
        q = query.Query(
            api,
            'SELECT+LogFile+FROM+EventLogFile',
            config,
            '52.0',
        )

        resp = q.execute(session)

        # verify
        self.assertEqual('SELECT+LogFile+FROM+EventLogFile', api.soql)
        self.assertEqual(api.query_api_ver, '52.0')
        self.assertIsNotNone(resp)
        self.assertTrue(type(resp) is dict)
        self.assertTrue('foo' in resp)
        self.assertEqual(resp['foo'], 'bar')


class TestQueryFactory(unittest.TestCase):
    def test_build_args_creates_expected_dict(self):
        '''
        build_args() returns dictionary with expected properties
        given: a query factory
        and given: a time lag value
        and given: a timestamp
        and given: a generation interval value
        when: build_args() is called
        then: return dict with expected properties
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
        and given: a query dict
        when: get_env() is called
        and when: there is no env property in the query dict
        then: return an empty dict
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
        and given: a query dict
        when: get_env() is called
        and when: there is an env property in the query dict
        and when: the env property is not a dict
        then: return an empty dict
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
        and given: a query dict
        when: get_env() is called
        and when: there is an env property in the query dict
        and when: the env property is a dict
        then: return the env dict
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
        and given: a query dict
        and given: a lag time value
        and given: a timestamp
        and given: a generation interval value
        when: new() is called
        then: return a query instance with the input query with arguments replaced and URL encoded
        '''

        # setup
        _now = datetime.utcnow()

        def _utcnow():
            nonlocal _now
            return _now

        util._UTCNOW = _utcnow

        api = ApiStub()
        to_timestamp = util.get_iso_date_with_offset(time_lag_minutes=500)
        last_to_timestamp = util.get_iso_date_with_offset(time_lag_minutes=1000)
        now = _now.isoformat(timespec='milliseconds') + "Z"
        env = { 'foo': 'now()' }

        # execute
        f = query.QueryFactory()
        q = f.new(
            api,
            {
                'query': 'SELECT LogFile FROM EventLogFile WHERE CreatedDate>={from_timestamp} AND CreatedDate<{to_timestamp} AND LogIntervalType={log_interval_type} AND Foo={foo}',
                'env': env,
            },
            500,
            last_to_timestamp,
            'Daily',
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
        and given: a query dict
        and given: a lag time value
        and given: a timestamp
        and given: a generation interval value
        when: new() is called
        then: return a query instance with a config equal to the input query dict minus the query property
        '''

        # setup
        last_to_timestamp = util.get_iso_date_with_offset(time_lag_minutes=1000)

        # execute
        api = ApiStub()
        f = query.QueryFactory()
        q = f.new(
            api,
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
        and given: a query dict
        and given: a lag time value
        and given: a timestamp
        and given: a generation interval value
        when: new() is called
        and when: an api version is specified in the query dict
        then: return a query instance with the api version specified in the query dict
        '''

        # setup
        api = ApiStub(api_ver='54.0')
        last_to_timestamp = util.get_iso_date_with_offset(time_lag_minutes=1000)

        # execute
        f = query.QueryFactory()
        q = f.new(
            api,
            {
                'query': 'SELECT LogFile FROM EventLogFile',
                'api_ver': '58.0'
            },
            500,
            last_to_timestamp,
            'Daily',
        )

        # verify
        self.assertEqual(q.api_ver, '58.0')

    def test_new_returns_query_obj_with_default_api_ver(self):
        '''
        new() returns a query instance without an api version
        given: a query factory
        and given: a query dict
        and given: a lag time value
        and given: a timestamp
        and given: a generation interval value
        when: new() is called
        and when: no api version is specified in the query dict
        then: return a query instance without an api version
        '''

        # setup
        api = ApiStub(api_ver='54.0')
        last_to_timestamp = util.get_iso_date_with_offset(time_lag_minutes=1000)

        # execute
        f = query.QueryFactory()
        q = f.new(
            api,
            {
                'query': 'SELECT LogFile FROM EventLogFile',
            },
            500,
            last_to_timestamp,
            'Daily',
        )

        # verify
        self.assertIsNone(q.api_ver)
