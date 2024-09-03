from datetime import datetime
import unittest

from newrelic_logging import LoginException, SalesforceApiException
from newrelic_logging import config as mod_config, util, query
from . import \
    ApiStub, \
    SessionStub

class TestQuery(unittest.TestCase):
    def test_is_valid_records_response_returns_false_given_response_is_none(self):
        '''
        is_valid_records_response() returns false when the response is None
        given: the query API response is None
        when: is_valid_records_response() is called
        then: return False
        '''

        # execute
        b = query.is_valid_records_response(None)

        # verify
        self.assertFalse(b)

    def test_is_valid_records_response_returns_false_given_response_has_no_records(self):
        '''
        is_valid_records_response() returns false when the response has no 'records' property
        given: a query API response
        when: the response has no 'records' property
        and when: is_valid_records_response() is called
        then: return False
        '''

        # execute
        b = query.is_valid_records_response({})

        # verify
        self.assertFalse(b)

    def test_is_valid_records_response_returns_false_given_response_has_records_but_type_is_not_list(self):
        '''
        is_valid_records_response() returns false when the response has a 'records' property but it is not a list
        given: a query API response
        when: the response has a 'records' property
        and when: the type of the 'records' property is not a list
        and when: is_valid_records_response() is called
        then: return False
        '''

        # execute
        b = query.is_valid_records_response({ 'records': 'foo' })

        # verify
        self.assertFalse(b)

    def test_is_valid_records_response_returns_true_given_valid_response(self):
        '''
        is_valid_records_response() returns true when the response has a 'records' property that is a list
        given: a query API response
        when: the response has a 'records' property
        and when: the 'records' property is a list
        and when: is_valid_records_response() is called
        then: return True
        '''

        # execute
        b = query.is_valid_records_response({ 'records': [] })

        # verify
        self.assertTrue(b)

    def test_has_more_records_returns_false_given_valid_response_but_done_missing(self):
        '''
        has_more_records() returns false when the response is valid but it has no 'done' property
        given: a valid query API response
        when: the response has no 'done' property
        and when: has_more_records() is called
        then: return False
        '''

        # execute
        b = query.has_more_records({})

        # verify
        self.assertFalse(b)

    def test_has_more_records_returns_false_given_valid_response_but_next_records_url_missing(self):
        '''
        has_more_records() returns false when the response is valid but it has no 'nextRecordsUrl' property
        given: a valid query API response
        when: the response has a 'done' property
        and when: the response has no 'nextRecordsUrl' property
        when: has_more_records() is called
        then: return False
        '''

        # execute
        b = query.has_more_records({ 'done': False })

        # verify
        self.assertFalse(b)

    def test_has_more_records_returns_false_given_valid_response_and_done_is_true(self):
        '''
        has_more_records() returns false when the response is valid and 'done' is True
        given: a valid query API response
        when: the response has a 'done' property
        and when: the response has a 'nextRecordsUrl' property
        and when: the 'done' property is True
        when: has_more_records() is called
        then: return False
        '''

        # execute
        b = query.has_more_records({ 'done': True, 'nextRecordsUrl': 'foo' })

        # verify
        self.assertFalse(b)

    def test_has_more_records_returns_false_given_valid_response_but_next_records_url_is_empty(self):
        '''
        has_more_records() returns false when the response is valid but 'nextRecordsUrl' is the empty string
        given: a valid query API response
        when: the response has a 'done' property
        and when: the response has a 'nextRecordsUrl' property
        and when: the 'done' property is False
        and when: the 'nextRecordsUrl' property is the empty string
        when: has_more_records() is called
        then: return False
        '''

        # execute
        b = query.has_more_records({ 'done': False, 'nextRecordsUrl': '' })

        # verify
        self.assertFalse(b)

    def test_has_more_records_returns_true_given_valid_response_and_done_is_false_and_next_records_url_is_not_empty(self):
        '''
        has_more_records() returns true when the response is valid, 'done' is False, and 'nextRecordsUrl' is not the empty string
        given: a valid query API response
        when: the response has a 'done' property
        and when: the response has a 'nextRecordsUrl' property
        and when: the 'done' property is False
        and when: the 'nextRecordsUrl' property is not the empty string
        when: has_more_records() is called
        then: return True
        '''

        # execute
        b = query.has_more_records({ 'done': False, 'nextRecordsUrl': 'foo' })

        # verify
        self.assertTrue(b)

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
            resp = q.execute(session)
            # Have to use next to cause the generator to execute the function
            # else query() won't get executed and our stub won't have
            # a chance to throw the fake exception.
            next(resp)

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
            resp = q.execute(session)
            # Have to use next to cause the generator to execute the function
            # else query() won't get executed and our stub won't have
            # a chance to throw the fake exception.
            next(resp)

    def test_execute_calls_query_api_with_query_and_api_ver_and_yields_result(self):
        '''
        execute() calls api.query() with the given session, query string, and api version and returns a generator over the results
        given: an api instance
        and given: a query string
        and given: a configuration
        and given: an api version
        and given: an http session
        when: execute() is called
        then: calls api.query() with the given session, query string, and api version
        and when: the result is a valid response
        then: return a result generator
        '''

        # setup
        api = ApiStub(query_result={ 'records': [ { 'foo': 'bar' } ] })
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
        record = next(resp)

        # verify
        self.assertEqual('SELECT+LogFile+FROM+EventLogFile', api.soql)
        self.assertEqual(api.query_api_ver, '52.0')
        self.assertIsNotNone(resp)
        self.assertIsNotNone(record)
        self.assertTrue(type(record) is dict)
        self.assertTrue('foo' in record)
        self.assertEqual(record['foo'], 'bar')

    def test_execute_calls_query_api_with_query_and_yields_nothing_given_invalid_response(self):
        '''
        execute() calls api.query() with the given session, query string, and no api version and returns an "empty" generator when the result is not a valid response
        given: an api instance
        and given: a query string
        and given: a configuration
        and given: an http session
        when: execute() is called
        then: calls api.query() with the given session, query string, and no api version
        and when: the result is not a valid response
        then: return an "empty" result generator
        '''

        # setup
        api = ApiStub(query_result={})
        config = mod_config.Config({})
        session = SessionStub()

        # execute
        q = query.Query(
            api,
            'SELECT+LogFile+FROM+EventLogFile',
            config,
        )

        resp = q.execute(session)
        record = next(resp, None)

        # verify
        self.assertEqual('SELECT+LogFile+FROM+EventLogFile', api.soql)
        self.assertIsNone(api.query_api_ver)
        self.assertIsNotNone(resp)
        self.assertIsNone(record)

    def test_execute_calls_query_api_with_query_and_yields_all_given_single_page_of_results(self):
        '''
        execute() calls api.query() with the given session, query string, and no api version and returns a generator over the results when there is a single page of results
        given: an api instance
        and given: a query string
        and given: a configuration
        and given: an http session
        when: execute() is called
        then: calls api.query() with the given session, query string, and no api version
        and when: the response is valid
        and when: there is a single page of results
        then: return a generator over the results.
        '''

        # setup
        api = ApiStub(query_result={
            'done': True,
            'nextRecordsUrl': '',
            'records': [ { 'foo': 'bar' } ],
        })
        config = mod_config.Config({})
        session = SessionStub()

        # execute
        q = query.Query(
            api,
            'SELECT+LogFile+FROM+EventLogFile',
            config,
        )

        resp = q.execute(session)
        records = []
        for rec in resp:
            records.append(rec)

        # verify
        self.assertEqual('SELECT+LogFile+FROM+EventLogFile', api.soql)
        self.assertIsNone(api.query_api_ver)
        self.assertIsNotNone(resp)
        self.assertEqual(len(records), 1)
        self.assertTrue(type(records[0]) is dict)
        self.assertTrue('foo' in records[0])
        self.assertEqual(records[0]['foo'], 'bar')

    def test_execute_calls_query_api_with_query_and_yields_all_given_multiple_pages_of_results(self):
        '''
        execute() calls api.query() with the given session, query string, and no api version and returns a generator over all pages of results when there are multiple pages of results
        given: an api instance
        and given: a query string
        and given: a configuration
        and given: an http session
        when: execute() is called
        then: calls api.query() with the given session, query string, and no api version
        and when: the response is valid
        and when: there are multiple pages of results
        then: return a generator over all pages of results.
        '''

        # setup
        api = ApiStub(query_result={
            'done': False,
            'nextRecordsUrl': '/more1',
            'records': [ { 'foo': 'bar' } ],
            '/more1': {
                'done': False,
                'nextRecordsUrl': '/more2',
                'records': [ { 'beep': 'boop' } ],
            },
            '/more2': {
                'done': False,
                'nextRecordsUrl': '/more3',
                'records': [ { 'bip': 'bop' } ],
            },
            '/more3': {
                'done': False,
                'nextRecordsUrl': '/more4',
                'records': [ { 'one': 'two' } ],
            },
            '/more4': {
                'done': True,
                'nextRecordsUrl': '',
                'records': [ { 'this': 'that' } ],
            },
        })
        config = mod_config.Config({})
        session = SessionStub()

        # execute
        q = query.Query(
            api,
            'SELECT+LogFile+FROM+EventLogFile',
            config,
        )

        resp = q.execute(session)
        records = []
        for rec in resp:
            records.append(rec)

        # verify
        self.assertEqual('SELECT+LogFile+FROM+EventLogFile', api.soql)
        self.assertIsNone(api.query_api_ver)
        self.assertIsNotNone(resp)
        self.assertEqual(len(records), 5)
        self.assertTrue(type(records[0]) is dict)
        self.assertTrue('foo' in records[0])
        self.assertEqual(records[0]['foo'], 'bar')
        self.assertTrue(type(records[1]) is dict)
        self.assertTrue('beep' in records[1])
        self.assertEqual(records[1]['beep'], 'boop')
        self.assertTrue(type(records[2]) is dict)
        self.assertTrue('bip' in records[2])
        self.assertEqual(records[2]['bip'], 'bop')
        self.assertTrue(type(records[3]) is dict)
        self.assertTrue('one' in records[3])
        self.assertEqual(records[3]['one'], 'two')
        self.assertTrue(type(records[4]) is dict)
        self.assertTrue('this' in records[4])
        self.assertEqual(records[4]['this'], 'that')

    def test_execute_calls_query_api_with_query_and_yields_all_given_multiple_pages_of_results_with_invalid_last_result(self):
        '''
        execute() calls api.query() with the given session, query string, and no api version and returns a generator over all pages of results when there are multiple pages of results and ends when an invalid set of results is encountered
        given: an api instance
        and given: a query string
        and given: a configuration
        and given: an http session
        when: execute() is called
        then: calls api.query() with the given session, query string, and no api version
        and when: the response is valid
        and when: there are multiple pages of results
        and when: an invalid set of results is encountered
        the: return a generator over all pages of the response up to the invalid set of results
        '''

        # setup
        api = ApiStub(query_result={
            'done': False,
            'nextRecordsUrl': '/more1',
            'records': [ { 'foo': 'bar' } ],
            '/more1': {
                'done': False,
                'nextRecordsUrl': '/more2',
                'records': [ { 'beep': 'boop' } ],
            },
            '/more2': {
                'done': False,
                'nextRecordsUrl': '/more3',
                'records': [ { 'bip': 'bop' } ],
            },
            '/more3': {
            },
        })
        config = mod_config.Config({})
        session = SessionStub()

        # execute
        q = query.Query(
            api,
            'SELECT+LogFile+FROM+EventLogFile',
            config,
        )

        resp = q.execute(session)
        records = []
        for rec in resp:
            records.append(rec)

        # verify
        self.assertEqual('SELECT+LogFile+FROM+EventLogFile', api.soql)
        self.assertIsNone(api.query_api_ver)
        self.assertIsNotNone(resp)
        self.assertEqual(len(records), 3)
        self.assertTrue(type(records[0]) is dict)
        self.assertTrue('foo' in records[0])
        self.assertEqual(records[0]['foo'], 'bar')
        self.assertTrue(type(records[1]) is dict)
        self.assertTrue('beep' in records[1])
        self.assertEqual(records[1]['beep'], 'boop')
        self.assertTrue(type(records[2]) is dict)
        self.assertTrue('bip' in records[2])
        self.assertEqual(records[2]['bip'], 'bop')

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
