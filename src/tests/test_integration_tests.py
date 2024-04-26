from datetime import datetime
import json
import yaml
import unittest


from . import \
    ApiStub, \
    AuthenticatorStub, \
    FactoryStub, \
    NewRelicStub, \
    QueryFactoryStub


from newrelic_logging import \
    config as mod_config, \
    factory, \
    util
from newrelic_logging.query import receiver as query_receiver
from newrelic_logging.limits import receiver as limits_receiver


class TestIntegrationTests(unittest.TestCase):
    def setUp(self):
        with open('./tests/sample_log_lines.csv') as stream:
            self.log_rows = stream.readlines()

        with open('./tests/sample_log_lines.json') as stream:
            self.log_lines = json.load(stream)

        with open('./tests/sample_event_records.json') as stream:
            self.event_records = json.load(stream)

        with open('./tests/sample_log_records.json') as stream:
            self.log_records = json.load(stream)

        with open('./tests/sample_limits.json') as stream:
            self.limits = json.load(stream)

        with open('./tests/sample_config_logs_to_logs.yml') as stream:
            self.config_logs_to_logs = yaml.load(stream, Loader=yaml.Loader)

        with open('./tests/sample_config_logs_to_events.yml') as stream:
            self.config_logs_to_events = yaml.load(stream, Loader=yaml.Loader)

        with open('./tests/sample_config_query_to_logs.yml') as stream:
            self.config_query_to_logs = yaml.load(stream, Loader=yaml.Loader)

        with open('./tests/sample_config_query_to_events.yml') as stream:
            self.config_query_to_events = yaml.load(stream, Loader=yaml.Loader)

        with open('./tests/sample_config_limits_to_logs.yml') as stream:
            self.config_limits_to_logs = yaml.load(stream, Loader=yaml.Loader)

        with open('./tests/sample_config_limits_to_events.yml') as stream:
            self.config_limits_to_events = yaml.load(stream, Loader=yaml.Loader)

    def test_integration_sends_logs_given_log_records(self):
        # setup
        new_relic = NewRelicStub()
        auth = AuthenticatorStub()
        api = ApiStub(
            auth,
            lines=self.log_rows,
            query_result={
                'records': self.log_records,
            }
        )

        f = factory.Factory()
        fs = FactoryStub(
            f,
            new_relic=new_relic,
            authenticator=auth,
            api=api,
        )

        query_factory = QueryFactoryStub(wrap=True)
        r = query_receiver.new_create_receiver_func(
            self.config_logs_to_logs,
            query_factory,
            {},
            0
        )

        timestamp1 = util.get_log_line_timestamp(self.log_lines[0])
        timestamp2 = util.get_log_line_timestamp(self.log_lines[1])

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)

        # execute
        i = fs.new_integration(
            fs,
            mod_config.Config(self.config_logs_to_logs),
            [r],
            set(),
        )
        i.run()

        # verify
        self.assertTrue(auth.authenticate_called)
        self.assertEqual(len(query_factory.queries), 1)
        self.assertEqual(
            query_factory.queries[0].wrapped.query,
            query_receiver.SALESFORCE_LOG_DATE_QUERY,
        )
        self.assertTrue(query_factory.queries[0].executed)
        self.assertEqual(len(new_relic.logs), 1)
        self.assertEqual(len(new_relic.logs[0]), 1)

        self.assertTrue('common' in new_relic.logs[0][0])
        common = new_relic.logs[0][0]['common']
        self.assertTrue('environment' in common)
        self.assertEqual(common['environment'], 'staging')

        self.assertTrue('logs' in new_relic.logs[0][0])
        self.assertEqual(len(new_relic.logs[0][0]['logs']), 4)

        logs = new_relic.logs[0][0]['logs']
        l = logs[0]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'LogFile 00001111AAAABBBB row 0')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('EVENT_TYPE' in attrs)
        self.assertEqual(attrs['EVENT_TYPE'], 'ApexCallout')
        self.assertEqual(attrs['USER_ID'], '000000001111111')
        self.assertEqual(attrs['RUN_TIME'], '2112')
        self.assertEqual(attrs['CPU_TIME'], '10')
        self.assertEqual(attrs['timestamp'], timestamp1)
        self.assertEqual(l['timestamp'], timestamp1)

        l = logs[1]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'LogFile 00001111AAAABBBB row 1')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('EVENT_TYPE' in attrs)
        self.assertEqual(attrs['EVENT_TYPE'], 'ApexCallout')
        self.assertEqual(attrs['USER_ID'], '111111110000000')
        self.assertEqual(attrs['RUN_TIME'], '5150')
        self.assertEqual(attrs['CPU_TIME'], '20')
        self.assertEqual(attrs['timestamp'], timestamp2)
        self.assertEqual(l['timestamp'], timestamp2)

        l = logs[2]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'LogFile 00002222AAAABBBB row 0')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('EVENT_TYPE' in attrs)
        self.assertEqual(attrs['EVENT_TYPE'], 'ApexCallout')
        self.assertEqual(attrs['USER_ID'], '000000001111111')
        self.assertEqual(attrs['RUN_TIME'], '2112')
        self.assertEqual(attrs['CPU_TIME'], '10')
        self.assertEqual(attrs['timestamp'], timestamp1)
        self.assertEqual(l['timestamp'], timestamp1)

        l = logs[3]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'LogFile 00002222AAAABBBB row 1')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('EVENT_TYPE' in attrs)
        self.assertEqual(attrs['EVENT_TYPE'], 'ApexCallout')
        self.assertEqual(attrs['USER_ID'], '111111110000000')
        self.assertEqual(attrs['RUN_TIME'], '5150')
        self.assertEqual(attrs['CPU_TIME'], '20')
        self.assertEqual(attrs['timestamp'], timestamp2)
        self.assertEqual(l['timestamp'], timestamp2)

    def test_integration_sends_events_given_log_records(self):
        # setup
        new_relic = NewRelicStub()
        auth = AuthenticatorStub()
        api = ApiStub(
            auth,
            lines=self.log_rows,
            query_result={
                'records': self.log_records,
            }
        )

        f = factory.Factory()
        fs = FactoryStub(
            f,
            new_relic=new_relic,
            authenticator=auth,
            api=api,
        )

        query_factory = QueryFactoryStub(wrap=True)
        r = query_receiver.new_create_receiver_func(
            self.config_logs_to_events,
            query_factory,
            {},
            0
        )

        timestamp1 = util.get_log_line_timestamp(self.log_lines[0])
        timestamp2 = util.get_log_line_timestamp(self.log_lines[1])

        # preconditions
        self.assertEqual(len(new_relic.events), 0)

        # execute
        i = fs.new_integration(
            fs,
            mod_config.Config(self.config_logs_to_events),
            [r],
            set(),
        )
        i.run()

        # verify
        self.assertTrue(auth.authenticate_called)
        self.assertEqual(len(query_factory.queries), 1)
        self.assertEqual(
            query_factory.queries[0].wrapped.query,
            query_receiver.SALESFORCE_LOG_DATE_QUERY,
        )
        self.assertTrue(query_factory.queries[0].executed)
        self.assertEqual(len(new_relic.events), 1)
        events = new_relic.events[0]
        self.assertEqual(len(events), 4)

        attrs = events[0]
        self.assertTrue('eventType' in attrs)
        self.assertEqual(attrs['eventType'], 'ApexCallout')
        self.assertEqual(attrs['USER_ID'], '000000001111111')
        self.assertEqual(attrs['RUN_TIME'], '2112')
        self.assertEqual(attrs['CPU_TIME'], '10')
        self.assertEqual(attrs['timestamp'], timestamp1)
        self.assertEqual(attrs['environment'], 'staging')

        attrs = events[1]
        self.assertTrue('EVENT_TYPE' in attrs)
        self.assertEqual(attrs['EVENT_TYPE'], 'ApexCallout')
        self.assertEqual(attrs['USER_ID'], '111111110000000')
        self.assertEqual(attrs['RUN_TIME'], '5150')
        self.assertEqual(attrs['CPU_TIME'], '20')
        self.assertEqual(attrs['timestamp'], timestamp2)
        self.assertEqual(attrs['environment'], 'staging')

        attrs = events[2]
        self.assertTrue('EVENT_TYPE' in attrs)
        self.assertEqual(attrs['EVENT_TYPE'], 'ApexCallout')
        self.assertEqual(attrs['USER_ID'], '000000001111111')
        self.assertEqual(attrs['RUN_TIME'], '2112')
        self.assertEqual(attrs['CPU_TIME'], '10')
        self.assertEqual(attrs['timestamp'], timestamp1)
        self.assertEqual(attrs['environment'], 'staging')

        attrs = events[3]
        self.assertTrue('EVENT_TYPE' in attrs)
        self.assertEqual(attrs['EVENT_TYPE'], 'ApexCallout')
        self.assertEqual(attrs['USER_ID'], '111111110000000')
        self.assertEqual(attrs['RUN_TIME'], '5150')
        self.assertEqual(attrs['CPU_TIME'], '20')
        self.assertEqual(attrs['timestamp'], timestamp2)
        self.assertEqual(attrs['environment'], 'staging')

    def test_integration_sends_logs_given_query_records(self):
        # setup
        new_relic = NewRelicStub()
        auth = AuthenticatorStub()
        api = ApiStub(
            auth,
            query_result={
                'records': self.event_records,
            }
        )

        f = factory.Factory()
        fs = FactoryStub(
            f,
            new_relic=new_relic,
            authenticator=auth,
            api=api,
        )

        query_factory = QueryFactoryStub(wrap=True)
        r = query_receiver.new_create_receiver_func(
            self.config_query_to_logs,
            query_factory,
            {},
            0
        )

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)

        # execute
        i = fs.new_integration(
            fs,
            mod_config.Config(self.config_query_to_logs),
            [r],
            set(),
        )
        i.run()

        # verify
        self.assertTrue(auth.authenticate_called)
        self.assertEqual(len(query_factory.queries), 1)
        self.assertEqual(
            query_factory.queries[0].wrapped.query,
            'SELECT * FROM Account',
        )
        self.assertTrue(query_factory.queries[0].executed)
        self.assertEqual(len(new_relic.logs), 1)
        self.assertEqual(len(new_relic.logs[0]), 1)

        self.assertTrue('common' in new_relic.logs[0][0])
        common = new_relic.logs[0][0]['common']
        self.assertTrue('environment' in common)
        self.assertEqual(common['environment'], 'staging')

        self.assertTrue('logs' in new_relic.logs[0][0])
        self.assertEqual(len(new_relic.logs[0][0]['logs']), 3)
        logs = new_relic.logs[0][0]['logs']

        l = logs[0]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'Account 2024-03-11T00:00:00.000+0000')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('Id' in attrs)
        self.assertEqual(attrs['Id'], '000012345')
        self.assertEqual(attrs['Name'], 'My Account')
        self.assertEqual(attrs['BillingCity'], None)
        self.assertEqual(attrs['CreatedDate'], '2024-03-11T00:00:00.000+0000')
        self.assertEqual(attrs['CreatedBy.Name'], 'Foo Bar')
        self.assertEqual(attrs['CreatedBy.Profile.Name'], 'Beep Boop')
        self.assertEqual(attrs['CreatedBy.UserType'], 'Bip Bop')
        timestamp = util.get_timestamp(attrs['CreatedDate'])
        self.assertEqual(attrs['timestamp'], timestamp)
        self.assertEqual(l['timestamp'], timestamp)

        l = logs[1]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'Account 2024-03-10T00:00:00.000+0000')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('Id' in attrs)
        self.assertEqual(attrs['Id'], '000054321')
        self.assertEqual(attrs['Name'], 'My Other Account')
        self.assertEqual(attrs['BillingCity'], None)
        self.assertEqual(attrs['CreatedDate'], '2024-03-10T00:00:00.000+0000')
        self.assertEqual(attrs['CreatedBy.Name'], 'Foo Bar')
        self.assertEqual(attrs['CreatedBy.Profile.Name'], 'Beep Boop')
        self.assertEqual(attrs['CreatedBy.UserType'], 'Bip Bop')
        timestamp = util.get_timestamp(attrs['CreatedDate'])
        self.assertEqual(attrs['timestamp'], timestamp)
        self.assertEqual(l['timestamp'], timestamp)

        l = logs[2]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'Account 2024-03-09T00:00:00.000+0000')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('Id' in attrs)
        id = util.generate_record_id(['Name'], attrs)
        self.assertEqual(attrs['Id'], id)
        self.assertEqual(attrs['Name'], 'My Last Account')
        self.assertEqual(attrs['BillingCity'], None)
        self.assertEqual(attrs['CreatedDate'], '2024-03-09T00:00:00.000+0000')
        self.assertEqual(attrs['CreatedBy.Name'], 'Foo Bar')
        self.assertEqual(attrs['CreatedBy.Profile.Name'], 'Beep Boop')
        self.assertEqual(attrs['CreatedBy.UserType'], 'Bip Bop')
        timestamp = util.get_timestamp(attrs['CreatedDate'])
        self.assertEqual(attrs['timestamp'], timestamp)
        self.assertEqual(l['timestamp'], timestamp)

    def test_integration_sends_events_given_query_records(self):
        # setup
        new_relic = NewRelicStub()
        auth = AuthenticatorStub()
        api = ApiStub(
            auth,
            query_result={
                'records': self.event_records,
            }
        )

        f = factory.Factory()
        fs = FactoryStub(
            f,
            new_relic=new_relic,
            authenticator=auth,
            api=api,
        )

        query_factory = QueryFactoryStub(wrap=True)
        r = query_receiver.new_create_receiver_func(
            self.config_query_to_events,
            query_factory,
            {},
            0
        )

        # preconditions
        self.assertEqual(len(new_relic.events), 0)

        # execute
        i = fs.new_integration(
            fs,
            mod_config.Config(self.config_query_to_events),
            [r],
            set(),
        )
        i.run()

        # verify
        self.assertTrue(auth.authenticate_called)
        self.assertEqual(len(query_factory.queries), 1)
        self.assertEqual(
            query_factory.queries[0].wrapped.query,
            'SELECT * FROM Account',
        )
        self.assertTrue(query_factory.queries[0].executed)
        self.assertEqual(len(new_relic.events), 1)
        self.assertEqual(len(new_relic.events[0]), 3)
        events = new_relic.events[0]

        attrs = events[0]
        self.assertTrue('Id' in attrs)
        self.assertEqual(attrs['Id'], '000012345')
        self.assertEqual(attrs['Name'], 'My Account')
        self.assertEqual(attrs['BillingCity'], None)
        self.assertEqual(attrs['CreatedDate'], '2024-03-11T00:00:00.000+0000')
        self.assertEqual(attrs['CreatedBy.Name'], 'Foo Bar')
        self.assertEqual(attrs['CreatedBy.Profile.Name'], 'Beep Boop')
        self.assertEqual(attrs['CreatedBy.UserType'], 'Bip Bop')
        timestamp = util.get_timestamp(attrs['CreatedDate'])
        self.assertEqual(attrs['timestamp'], timestamp)
        self.assertTrue('environment' in attrs)
        self.assertEqual(attrs['environment'], 'staging')

        attrs = events[1]
        self.assertTrue('Id' in attrs)
        self.assertEqual(attrs['Id'], '000054321')
        self.assertEqual(attrs['Name'], 'My Other Account')
        self.assertEqual(attrs['BillingCity'], None)
        self.assertEqual(attrs['CreatedDate'], '2024-03-10T00:00:00.000+0000')
        self.assertEqual(attrs['CreatedBy.Name'], 'Foo Bar')
        self.assertEqual(attrs['CreatedBy.Profile.Name'], 'Beep Boop')
        self.assertEqual(attrs['CreatedBy.UserType'], 'Bip Bop')
        timestamp = util.get_timestamp(attrs['CreatedDate'])
        self.assertEqual(attrs['timestamp'], timestamp)

        attrs = events[2]
        self.assertTrue('Id' in attrs)
        id = util.generate_record_id(['Name'], attrs)
        self.assertEqual(attrs['Id'], id)
        self.assertEqual(attrs['Name'], 'My Last Account')
        self.assertEqual(attrs['BillingCity'], None)
        self.assertEqual(attrs['CreatedDate'], '2024-03-09T00:00:00.000+0000')
        self.assertEqual(attrs['CreatedBy.Name'], 'Foo Bar')
        self.assertEqual(attrs['CreatedBy.Profile.Name'], 'Beep Boop')
        self.assertEqual(attrs['CreatedBy.UserType'], 'Bip Bop')
        timestamp = util.get_timestamp(attrs['CreatedDate'])
        self.assertEqual(attrs['timestamp'], timestamp)

    def test_integration_sends_logs_given_limits(self):
        # setup
        new_relic = NewRelicStub()
        auth = AuthenticatorStub()
        api = ApiStub(
            auth,
            limits_result=self.limits,
        )

        f = factory.Factory()
        fs = FactoryStub(
            f,
            new_relic=new_relic,
            authenticator=auth,
            api=api,
        )

        r = limits_receiver.new_create_receiver_func()

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)

        # execute
        i = fs.new_integration(
            fs,
            mod_config.Config(self.config_limits_to_logs),
            [r],
            set(),
        )
        i.run()

        # verify
        self.assertTrue(auth.authenticate_called)
        self.assertEqual(len(new_relic.logs), 1)
        self.assertEqual(len(new_relic.logs[0]), 1)
        self.assertTrue('common' in new_relic.logs[0][0])
        common = new_relic.logs[0][0]['common']
        self.assertTrue('environment' in common)
        self.assertEqual(common['environment'], 'staging')
        self.assertTrue('logs' in new_relic.logs[0][0])
        self.assertEqual(len(new_relic.logs[0][0]['logs']), 5)
        logs = new_relic.logs[0][0]['logs']

        l = logs[0]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'Salesforce Org Limit: ActiveScratchOrgs')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'ActiveScratchOrgs')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 3)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 3)

        l = logs[1]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'Salesforce Org Limit: AnalyticsExternalDataSizeMB')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'AnalyticsExternalDataSizeMB')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 40960)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 40960)

        l = logs[2]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'Salesforce Org Limit: ConcurrentAsyncGetReportInstances')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'ConcurrentAsyncGetReportInstances')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 200)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 200)

        l = logs[3]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'Salesforce Org Limit: ConcurrentEinsteinDataInsightsStoryCreation')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'ConcurrentEinsteinDataInsightsStoryCreation')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 5)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 5)

        l = logs[4]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'Salesforce Org Limit: ConcurrentEinsteinDiscoveryStoryCreation')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'ConcurrentEinsteinDiscoveryStoryCreation')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 2)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 2)

    def test_integration_sends_events_given_limits(self):
        # setup
        new_relic = NewRelicStub()
        auth = AuthenticatorStub()
        api = ApiStub(
            auth,
            limits_result=self.limits,
        )

        f = factory.Factory()
        fs = FactoryStub(
            f,
            new_relic=new_relic,
            authenticator=auth,
            api=api,
        )

        r = limits_receiver.new_create_receiver_func()

        # preconditions
        self.assertEqual(len(new_relic.events), 0)

        # execute
        i = fs.new_integration(
            fs,
            mod_config.Config(self.config_limits_to_events),
            [r],
            set(),
        )
        i.run()

        # verify
        self.assertTrue(auth.authenticate_called)
        self.assertEqual(len(new_relic.events), 1)
        self.assertEqual(len(new_relic.events[0]), 5)

        attrs = new_relic.events[0][0]
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'ActiveScratchOrgs')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 3)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 3)
        self.assertTrue('environment' in attrs)
        self.assertEqual(attrs['environment'], 'staging')

        attrs = new_relic.events[0][1]
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'AnalyticsExternalDataSizeMB')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 40960)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 40960)
        self.assertTrue('environment' in attrs)
        self.assertEqual(attrs['environment'], 'staging')

        attrs = new_relic.events[0][2]
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'ConcurrentAsyncGetReportInstances')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 200)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 200)
        self.assertTrue('environment' in attrs)
        self.assertEqual(attrs['environment'], 'staging')

        attrs = new_relic.events[0][3]
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'ConcurrentEinsteinDataInsightsStoryCreation')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 5)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 5)
        self.assertTrue('environment' in attrs)
        self.assertEqual(attrs['environment'], 'staging')

        attrs = new_relic.events[0][4]
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'ConcurrentEinsteinDiscoveryStoryCreation')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 2)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 2)
        self.assertTrue('environment' in attrs)
        self.assertEqual(attrs['environment'], 'staging')
