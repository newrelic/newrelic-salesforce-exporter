from datetime import datetime, timedelta
import unittest


from . import \
    ApiFactoryStub, \
    AuthenticatorStub, \
    DataCacheStub, \
    PipelineStub, \
    QueryStub, \
    QueryFactoryStub, \
    SessionStub
from newrelic_logging import \
    config, \
    salesforce, \
    util, \
    LoginException, \
    SalesforceApiException


class TestSalesforce(unittest.TestCase):
    def test_init(self):
        _now = datetime.utcnow()

        def _utcnow():
            nonlocal _now
            return _now

        util._UTCNOW = _utcnow

        '''
        given: an instance name and configuration, a data cache, authenticator,
               pipeline, query factory, initial delay value, and a set of
               queries
        when: values are present in the configuration for all relevant config
              properties
        and when: no data cache is specified
        and when: no queries are specified
        then: a new Salesforce instance is created with the correct values
        '''

        # setup
        time_lag_minutes = 603
        initial_delay = 5
        cfg = config.Config({
            'api_ver': '55.0',
            'time_lag_minutes': time_lag_minutes,
            'date_field': 'CreateDate',
            'generation_interval': 'Hourly',
        })
        auth = AuthenticatorStub()
        pipeline = PipelineStub()
        data_cache = DataCacheStub()
        api_factory = ApiFactoryStub()
        query_factory = QueryFactoryStub()
        last_to_timestamp = util.get_iso_date_with_offset(
            time_lag_minutes,
            initial_delay,
        )

        # execute
        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # verify
        self.assertEqual(client.instance_name, 'test_instance')
        self.assertEqual(client.data_cache, None)
        self.assertEqual(client.time_lag_minutes, time_lag_minutes)
        self.assertEqual(client.date_field, 'CreateDate')
        self.assertEqual(client.generation_interval, 'Hourly')
        self.assertEqual(client.last_to_timestamp, last_to_timestamp)
        self.assertIsNotNone(client.api)
        self.assertEqual(client.api.authenticator, auth)
        self.assertEqual(client.api.api_ver, '55.0')
        self.assertTrue(len(client.queries) == 1)
        self.assertTrue('query' in client.queries[0])
        self.assertEqual(
            client.queries[0]['query'],
            salesforce.SALESFORCE_CREATED_DATE_QUERY,
        )

        '''
        given: an instance name and configuration, a data cache, authenticator,
               pipeline, query factory, initial delay value, and a set of
               queries
        and when: no data cache is specified
        and when: no queries are specified
        and when: no lag time is specified in the config
        then: a new Salesforce instance is created with the default lag time
        '''

        # setup
        cfg = config.Config({
            'api_ver': '55.0',
            'date_field': 'CreateDate',
            'generation_interval': 'Hourly',
        })
        last_to_timestamp = util.get_iso_date_with_offset(
            config.DEFAULT_TIME_LAG_MINUTES,
            initial_delay,
        )

        # execute
        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # verify
        self.assertEqual(
            client.time_lag_minutes,
            config.DEFAULT_TIME_LAG_MINUTES,
        )
        self.assertEqual(client.last_to_timestamp, last_to_timestamp)

        '''
        given: an instance name and configuration, a data cache, authenticator,
               pipeline, query factory, initial delay value, and a set of
               queries
        and when: a data cache is specified
        and when: no queries are specified
        and when: no lag time is specified in the config
        then: a new Salesforce instance is created with the lag time set to 0
        '''

        # setup
        last_to_timestamp = util.get_iso_date_with_offset(
            0,
            initial_delay,
        )

        # execute
        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            data_cache,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # verify
        self.assertEqual(
            client.time_lag_minutes,
            0,
        )
        self.assertEqual(client.last_to_timestamp, last_to_timestamp)

        '''
        given: an instance name and configuration, a data cache, authenticator,
               pipeline, query factory, initial delay value, and a set of
               queries
        and when: no data cache is specified
        and when: no queries are specified
        and when: no date field is specified in the config
        then: a new Salesforce instance is created with the default date field
        '''

        # setup
        cfg = config.Config({
            'api_ver': '55.0',
            'time_lag_minutes': time_lag_minutes,
            'generation_interval': 'Hourly',
        })

        # execute
        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # verify
        self.assertEqual(client.date_field, config.DATE_FIELD_LOG_DATE)

        '''
        given: an instance name and configuration, a data cache, authenticator,
               pipeline, query factory, initial delay value, and a set of
               queries
        and when: a data cache is specified
        and when: no queries are specified
        and when: no date field is specified in the config
        then: a new Salesforce instance is created with the default date field
        '''

        # execute
        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            data_cache,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # verify
        self.assertEqual(client.date_field, config.DATE_FIELD_CREATE_DATE)

        '''
        given: an instance name and configuration, a data cache, authenticator,
               pipeline, query factory, initial delay value, and a set of
               queries
        and when: no data cache is specified
        and when: no queries are specified
        and when: no generation interval is specified
        then: a new Salesforce instance is created with the default generation
              interval
        '''

        # setup
        cfg = config.Config({
            'api_ver': '55.0',
            'time_lag_minutes': time_lag_minutes,
            'date_field': 'CreateDate'
        })

        # execute
        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # verify
        self.assertEqual(
            client.generation_interval,
            config.DEFAULT_GENERATION_INTERVAL,
        )

        '''
        given: an instance name and configuration, a data cache, authenticator,
               pipeline, query factory, initial delay value, and a set of
               queries
        and when: no data cache is specified
        and when: no queries are specified
        and when: the date field option is set to 'LogDate'
        then: a new Salesforce instance is created with the default log date
              query
        '''

        # setup
        cfg = config.Config({
            'api_ver': '55.0',
            'time_lag_minutes': time_lag_minutes,
            'date_field': 'LogDate',
            'generation_interval': 'Hourly',
        })

        # execute
        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # verify
        self.assertTrue(len(client.queries) == 1)
        self.assertTrue('query' in client.queries[0])
        self.assertEqual(
            client.queries[0]['query'],
            salesforce.SALESFORCE_LOG_DATE_QUERY,
        )

        '''
        given: an instance name and configuration, a data cache, authenticator,
               pipeline, query factory, initial delay value, and a set of
               queries
        and when: no data cache is specified
        and when: queries are specified
        then: a new Salesforce instance is created with the specified queries
        '''

        # setup
        queries = [ { 'query': 'foo' }, { 'query': 'bar' }]

        # execute
        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
            queries
        )

        # verify
        self.assertTrue(len(client.queries) == 2)
        self.assertTrue('query' in client.queries[0])
        self.assertEqual(client.queries[0]['query'], 'foo')
        self.assertTrue('query' in client.queries[1])
        self.assertEqual(client.queries[1]['query'], 'bar')

    def test_authenticate_is_called(self):
        '''
        given: an instance name and configuration, a data cache, authenticator,
               pipeline, query factory, initial delay value, set of queries,
               and an http session
        when: called
        then: the underlying api is called
        '''

        # setup
        time_lag_minutes = 603
        initial_delay = 5
        cfg = config.Config({
            'api_ver': '55.0',
            'time_lag_minutes': time_lag_minutes,
            'date_field': 'CreateDate',
            'generation_interval': 'Hourly',
        })
        auth = AuthenticatorStub()
        pipeline = PipelineStub()
        api_factory = ApiFactoryStub()
        query_factory = QueryFactoryStub()
        session = SessionStub()

        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # execute
        client.authenticate(session)

        # verify
        self.assertIsNotNone(client.api)
        self.assertEqual(client.api.authenticator, auth)
        self.assertTrue(auth.authenticate_called)

    def test_authenticate_raises_login_exception_if_authenticate_does(self):
        '''
        given: an instance name and configuration, a data cache, authenticator,
               pipeline, query factory, initial delay value, set of queries,
               and an http session
        when: called
        and when: authenticator.authenticate() raises a LoginException
        then: raise a LoginException
        '''

        # setup
        time_lag_minutes = 603
        initial_delay = 5
        cfg = config.Config({
            'api_ver': '55.0',
            'time_lag_minutes': time_lag_minutes,
            'date_field': 'CreateDate',
            'generation_interval': 'Hourly',
        })
        auth = AuthenticatorStub(raise_login_error=True)
        pipeline = PipelineStub()
        api_factory = ApiFactoryStub()
        query_factory = QueryFactoryStub()
        session = SessionStub()

        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # execute / verify
        with self.assertRaises(LoginException) as _:
            client.authenticate(session)

        # verify
        self.assertIsNotNone(client.api)
        self.assertEqual(client.api.authenticator, auth)
        self.assertTrue(auth.authenticate_called)

    def test_slide_time_range(self):
        _now = datetime.utcnow()

        def _utcnow():
            nonlocal _now
            return _now

        util._UTCNOW = _utcnow

        '''
        given: an instance name and configuration, data cache, authenticator,
               pipeline, query factory, initial delay value, and a set of
               queries
        when: called
        then: the 'last_to_timestamp' is updated
        '''

        # setup
        time_lag_minutes = 603
        initial_delay = 5
        cfg = config.Config({
            'api_ver': '55.0',
            'time_lag_minutes': time_lag_minutes,
            'date_field': 'CreateDate',
            'generation_interval': 'Hourly',
        })
        auth = AuthenticatorStub()
        pipeline = PipelineStub()
        api_factory = ApiFactoryStub()
        query_factory = QueryFactoryStub()

        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        last_to_before = client.last_to_timestamp

        # pretend it's 10 minutes from now to ensure this is different from
        # the timestamp calculated during object creation
        _now = datetime.utcnow() + timedelta(minutes=10)

        # execute
        client.slide_time_range()

        # verify
        last_to_after = client.last_to_timestamp

        self.assertNotEqual(last_to_after, last_to_before)

    def test_fetch_logs(self):
        '''
        given: an instance name and configuration, data cache, authenticator,
               pipeline, query factory, initial delay value, a set of queries,
               and an http session
        when: the set of queries is the empty set
        then: a default query should be executed
        '''

        # setup
        time_lag_minutes = 603
        initial_delay = 5
        cfg = config.Config({
            'api_ver': '55.0',
            'time_lag_minutes': time_lag_minutes,
            'date_field': 'CreateDate',
            'generation_interval': 'Hourly',
        })
        auth = AuthenticatorStub()
        pipeline = PipelineStub()
        api_factory = ApiFactoryStub()
        query_factory = QueryFactoryStub()
        session = SessionStub()

        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # execute
        client.fetch_logs(session)

        # verify

        self.assertEqual(len(query_factory.queries), 1)
        query = query_factory.queries[0]
        self.assertTrue(query.executed)
        self.assertTrue(pipeline.executed)
        self.assertEqual(len(pipeline.queries), 1)
        self.assertEqual(query, pipeline.queries[0])

        '''
        given: an instance name and configuration, data cache, authenticator,
               pipeline, query factory, initial delay value, a set of queries,
               and an http session
        when: the set of queries is not the empty set
        then: each query should be executed
        '''

        auth = AuthenticatorStub()
        pipeline = PipelineStub()
        query_factory = QueryFactoryStub()
        api_factory = ApiFactoryStub()
        session = SessionStub()
        queries = [
            {
                'query': 'foo',
            },
            {
                'query': 'bar',
            },
            {
                'query': 'beep',
            },
            {
                'query': 'boop',
            },
        ]

        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
            queries,
        )

        # execute
        client.fetch_logs(session)

        # verify

        self.assertEqual(len(query_factory.queries), 4)

        query1 = query_factory.queries[0]
        self.assertEqual(query1.query, 'foo')
        self.assertTrue(query1.executed)
        query2 = query_factory.queries[1]
        self.assertEqual(query2.query, 'bar')
        self.assertTrue(query2.executed)
        query3 = query_factory.queries[2]
        self.assertEqual(query3.query, 'beep')
        self.assertTrue(query3.executed)
        query4 = query_factory.queries[3]
        self.assertEqual(query4.query, 'boop')
        self.assertTrue(query4.executed)

        self.assertTrue(pipeline.executed)
        self.assertEqual(len(pipeline.queries), 4)
        self.assertEqual(query1, pipeline.queries[0])
        self.assertEqual(query2, pipeline.queries[1])
        self.assertEqual(query3, pipeline.queries[2])
        self.assertEqual(query4, pipeline.queries[3])

        '''
        given: an instance name and configuration, data cache, authenticator,
               pipeline, query factory, initial delay value, a set of queries,
               and an http session
        when: no response is returned from a query
        then: query should be executed and pipeline should not be executed
        '''

        auth = AuthenticatorStub()
        pipeline = PipelineStub()
        query = QueryStub(result=None)
        query_factory = QueryFactoryStub(query)
        api_factory = ApiFactoryStub()
        session = SessionStub()

        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # execute
        client.fetch_logs(session)

        # verify

        self.assertTrue(query.executed)
        self.assertFalse(pipeline.executed)

        '''
        given: an instance name and configuration, data cache, authenticator,
               pipeline, query factory, initial delay value, a set of queries,
               and an http session
        when: there is no 'records' attribute in response returned from query
        then: query should be executed and pipeline should not be executed
        '''

        auth = AuthenticatorStub()
        pipeline = PipelineStub()
        query = QueryStub(result={ 'foo': 'bar' })
        query_factory = QueryFactoryStub(query)
        api_factory = ApiFactoryStub()
        session = SessionStub()

        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # execute
        client.fetch_logs(session)

        # verify

        self.assertTrue(query.executed)
        self.assertFalse(pipeline.executed)

        '''
        given: an instance name and configuration, data cache, authenticator,
               pipeline, api factory, query factory, initial delay value, and an
               http session
        when: pipeline.execute() raises a LoginException
        then: raise a LoginException
        '''

        auth = AuthenticatorStub()
        pipeline = PipelineStub(raise_login_error=True)
        query = QueryStub()
        query_factory = QueryFactoryStub(query)
        api_factory = ApiFactoryStub()
        session = SessionStub()

        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # execute / verify
        with self.assertRaises(LoginException) as _:
            client.fetch_logs(session)

        '''
        given: an instance name and configuration, data cache, authenticator,
               pipeline, api factory, query factory, initial delay value, and an
               http session
        when: pipeline.execute() raises a SalesforceApiException
        then: raise a SalesforceApiException
        '''

        auth = AuthenticatorStub()
        pipeline = PipelineStub(raise_error=True)
        query = QueryStub()
        query_factory = QueryFactoryStub(query)
        api_factory = ApiFactoryStub()
        session = SessionStub()

        client = salesforce.SalesForce(
            'test_instance',
            cfg,
            None,
            auth,
            pipeline,
            api_factory,
            query_factory,
            initial_delay,
        )

        # execute / verify
        with self.assertRaises(SalesforceApiException) as _:
            client.fetch_logs(session)


if __name__ == '__main__':
    unittest.main()
