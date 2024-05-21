import copy
import json
import unittest


from newrelic_logging import \
    config as mod_config, \
    DataFormat, \
    LoginException, \
    NewRelicApiException, \
    pipeline, \
    SalesforceApiException
from . import \
    NewRelicStub, \
    ReceiverStub, \
    SessionStub


class TestPipeline(unittest.TestCase):
    def setUp(self):
        with open('./tests/sample_log_lines.csv') as stream:
            self.log_rows = stream.readlines()

        with open('./tests/sample_log_lines.json') as stream:
            self.log_lines = json.load(stream)

        with open('./tests/sample_event_records.json') as stream:
            self.event_records = json.load(stream)

        with open('./tests/sample_log_records.json') as stream:
            self.log_records = json.load(stream)


    def logs(self, n: int = 50):
        for i in range(0, n):
            yield {
                'message': f'log {i}',
                'attributes': {
                    'EVENT_TYPE': f'SFEvent{i}',
                    'REQUEST_ID': f'abcdef-{i}',
                },
            }

    def test_load_as_logs_sends_one_request_when_log_entries_less_than_max_rows(self):
        '''
        load_as_logs() sends a single Logs API request when the number of log entries is less than max rows
        given: an iterator over log entries
        and given: a NewRelic instance
        and given: a dict of key:value pairs to use as labels
        and given: a max rows value
        when: load_as_logs() is called
        and when: the number of log entries to send is less than max rows
        then: a single Logs API request is made
        and: the payload has a 'common' property with all the labels
        and: the payload has a 'logs' property with all the log entries
        '''

        # setup
        labels = { 'foo': 'bar' }
        new_relic = NewRelicStub()

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)

        # execute
        pipeline.load_as_logs(
            self.logs(),
            new_relic,
            labels,
            pipeline.DEFAULT_MAX_ROWS,
        )

        # verify
        self.assertEqual(len(new_relic.logs), 1)
        l = new_relic.logs[0]
        self.assertEqual(len(l), 1)
        l = l[0]
        self.assertTrue('logs' in l)
        self.assertTrue('common' in l)
        self.assertTrue(type(l['common']) is dict)
        self.assertTrue('foo' in l['common'])
        self.assertEqual(l['common']['foo'], 'bar')
        self.assertEqual(len(l['logs']), 50)
        for i, log in enumerate(l['logs']):
            self.assertTrue('message' in log)
            self.assertEqual(log['message'], f'log {i}')
            self.assertTrue('attributes' in log)
            self.assertTrue('EVENT_TYPE' in log['attributes'])
            self.assertEqual(log['attributes']['EVENT_TYPE'], f'SFEvent{i}')
            self.assertTrue('REQUEST_ID' in log['attributes'])
            self.assertEqual(log['attributes']['REQUEST_ID'], f'abcdef-{i}')

    def test_load_as_logs_sends_multiple_requests_when_log_entries_is_a_multiple_of_max_rows(self):
        '''
        load_as_logs() sends n / max Logs API requests when the number of log entries is a factor of max rows
        given: an iterator over log entries
        and given: a NewRelic instance
        and given: a dict of key:value pairs to use as labels
        and given: a max rows value
        when: load_as_logs() is called
        and when: the number of log entries to send is a factor of max rows
        then: n / max Logs API requests are made
        and: each of the payloads contains max logs
        and: each has a 'common' property with all the labels
        and: the payload has a 'logs' property with all the log entries
        '''

        # setup
        labels = { 'foo': 'bar' }
        new_relic = NewRelicStub()

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)

        # execute
        pipeline.load_as_logs(
            self.logs(150),
            new_relic,
            labels,
            50,
        )

        # verify
        self.assertEqual(len(new_relic.logs), 3)
        for i in range(0, 3):
            l = new_relic.logs[i]
            self.assertEqual(len(l), 1)
            l = l[0]
            self.assertTrue('logs' in l)
            self.assertTrue('common' in l)
            self.assertEqual(len(l['logs']), 50)

    def test_load_as_logs_sends_multiple_requests_when_log_entries_greater_than_max_rows(self):
        '''
        load_as_logs() sends floor(n / max) + 1 Logs API requests when the number of log entries is greater than max rows but not a multiple
        given: an iterator over log entries
        and given: a NewRelic instance
        and given: a dict of key:value pairs to use as labels
        and given: a max rows value
        when: load_as_logs() is called
        and when: the number of log entries to send is greater than max rows but
            not a multiple
        then: floor(n / max) + 1 Logs API requests are made
        and: each of floor(n / max) payloads contains max logs
        and: each has a 'common' property with all the labels
        and: the payload has a 'logs' property with all the log entries
        and: one additional post is made containing n % max logs
        '''

        # setup
        labels = { 'foo': 'bar' }
        new_relic = NewRelicStub()

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)

        # execute
        pipeline.load_as_logs(
            self.logs(53),
            new_relic,
            labels,
            50,
        )

        # verify
        self.assertEqual(len(new_relic.logs), 2)
        l = new_relic.logs[0]
        self.assertEqual(len(l), 1)
        l = l[0]
        self.assertTrue('logs' in l)
        self.assertTrue('common' in l)
        self.assertEqual(len(l['logs']), 50)
        l = new_relic.logs[1]
        self.assertEqual(len(l), 1)
        l = l[0]
        self.assertTrue('logs' in l)
        self.assertTrue('common' in l)
        self.assertEqual(len(l['logs']), 3)

    def test_pack_log_into_event_returns_event_given_log_labels_and_empty_numeric_fields_set(self):
        '''
        pack_log_into_event() return an event with properties for each attribute in the given log entry and an event type where no attributes are converted to numeric values
        given: a single log entry
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        when: pack_log_into_event() is called
        and when: the set of numeric field names is the empty set
        and when: the log entry contains an 'EVENT_TYPE' property
        then: return a single event with a property for each attribute specified
            in the 'attributes' field of the log
        and: an 'eventType' property set to the value of the `EVENT_TYPE`
            property of the log entry
        '''

        # setup
        log = {
            'message': 'Foo and Bar',
            'attributes': self.log_lines[0]
        }

        # execute
        event = pipeline.pack_log_into_event(
            log,
            { 'foo': 'bar' },
            set(),
        )

        # verify
        self.assertTrue('eventType' in event)
        self.assertEqual(event['eventType'], self.log_lines[0]['EVENT_TYPE'])
        self.assertTrue('foo' in event)
        self.assertEqual(event['foo'], 'bar')
        self.assertEqual(len(event), len(self.log_lines[0]) + 2)
        for k in self.log_lines[0]:
            self.assertTrue(k in event)
            self.assertEqual(event[k], self.log_lines[0][k])

    def test_pack_log_into_event_returns_event_given_log_labels_and_numeric_fields_set(self):
        '''
        pack_log_into_event() return an event with properties for each attribute in the given log entry and an event type where specified attributes are converted to numeric values
        given: a single log entry
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        when: pack_log_into_event() is called
        and when: the set of numeric field names is not empty
        and when: the log entry contains an 'EVENT_TYPE' property
        then: return a single event with a property for each attribute specified
            in the 'attributes' field of the log
        and: an 'eventType' property set to the value of the `EVENT_TYPE`
            property of the log entry
        and: attribute values for fields specified in the numeric fields set
            are converted to numeric values
        '''

        # setup
        log = {
            'message': 'Foo and Bar',
            'attributes': self.log_lines[0]
        }

        # execute
        event = pipeline.pack_log_into_event(
            log,
            { 'foo': 'bar' },
            set(['RUN_TIME', 'CPU_TIME', 'SUCCESS', 'URI']),
        )

        # verify
        self.assertEqual(len(event), len(self.log_lines[0]) + 2)
        self.assertTrue(type(event['RUN_TIME']) == int)
        self.assertTrue(type(event['CPU_TIME']) == int)
        self.assertTrue(type(event['SUCCESS']) == int)
        self.assertTrue(type(event['URI']) == str)

    def test_pack_log_into_event_returns_event_with_default_event_type_given_log_labels_and_empty_numeric_fields_set(self):
        '''
        pack_log_into_event() return an event with properties for each attribute in the given log entry and the default event type where no attributes are converted to numeric values
        given: a single log entry
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        when: pack_log_into_event() is called
        and when: the set of numeric field names is the empty set
        and when: the log entry does not contain an 'EVENT_TYPE' property
        then: return a single event with a property for each attribute specified
            in the 'attributes' field of the log
        and: an 'eventType' property set to the default event type
        '''

        # setup
        log_lines = copy.deepcopy(self.log_lines)

        del log_lines[0]['EVENT_TYPE']

        log = {
            'message': 'Foo and Bar',
            'attributes': log_lines[0]
        }

        # execute
        event = pipeline.pack_log_into_event(
            log,
            { 'foo': 'bar' },
            set(),
        )

        # verify
        self.assertEqual(len(event), len(log_lines[0]) + 2)
        self.assertTrue('eventType' in event)
        self.assertEqual(event['eventType'], 'UnknownSFEvent')

    def test_load_as_events_sends_one_request_when_log_entries_less_than_max_rows(self):
        '''
        load_as_events() sends a single Events API request when the number of log entries is less than max rows
        given: an iterator over log entries
        and given: a NewRelic instance
        and given: a dict of key:value pairs to use as labels
        and given: a max rows value
        and given: a set of numeric field names
        when: load_as_events() is called
        and when: the set of numeric field names is the empty set
        and when: the number of log entries to send is less than max rows
        then: a single Events API request is made
        and: one event is sent for each log entry
        and: each event has an attribute for each label
        '''

        # setup
        labels = { 'foo': 'bar' }
        new_relic = NewRelicStub()

        # preconditions
        self.assertEqual(len(new_relic.events), 0)

        # execute
        pipeline.load_as_events(
            self.logs(),
            new_relic,
            labels,
            pipeline.DEFAULT_MAX_ROWS,
            set(),
        )

        # verify
        self.assertEqual(len(new_relic.events), 1)
        l = new_relic.events[0]
        self.assertEqual(len(l), 50)
        for i, event in enumerate(l):
            self.assertTrue('foo' in event)
            self.assertEqual(event['foo'], 'bar')
            self.assertTrue('EVENT_TYPE' in event)
            self.assertEqual(event['EVENT_TYPE'], f'SFEvent{i}')
            self.assertTrue('REQUEST_ID' in event)
            self.assertEqual(event['REQUEST_ID'], f'abcdef-{i}')

    def test_load_as_events_sends_multiple_requests_when_log_entries_is_a_multiple_of_max_rows(self):
        '''
        load_as_events() sends n / max Events API requests when the number of log entries is a multiple of max rows
        given: an iterator over log entries
        and given: a NewRelic instance
        and given: a dict of key:value pairs to use as labels
        and given: a max rows value
        and given: a set of numeric field names
        when: load_as_events() is called
        and when: the number of log entries to send is a multiple of max rows
        then: n / max Events API requests are made
        and: each of the payloads contains max events
        and: each event has an attribute for each label
        '''

        # setup
        labels = { 'foo': 'bar' }
        new_relic = NewRelicStub()

        # preconditions
        self.assertEqual(len(new_relic.events), 0)

        # execute
        pipeline.load_as_events(
            self.logs(150),
            new_relic,
            labels,
            50,
            set(),
        )

        # verify
        self.assertEqual(len(new_relic.events), 3)
        for i in range(0, 3):
            l = new_relic.events[i]
            self.assertEqual(len(l), 50)

    def test_load_as_events_sends_multiple_requests_when_log_entries_greater_than_max_rows(self):
        '''
        load_as_events() sends floor(n / max) + 1 Events API requests when the number of log entries is greater than max rows but not a multiple
        given: an iterator over log entries
        and given: a NewRelic instance
        and given: a dict of key:value pairs to use as labels
        and given: a max rows value
        and given: a set of numeric field names
        when: load_as_events() is called
        and when: the number of log entries to send is greater than max rows but
            not a multiple
        then: floor(n / max) + 1 Events API requests are made
        and: each of floor(n / max) payloads contains max events
        and: each event has an attribute for each label
        and: one additional post is made containing n % max events
        '''

        # setup
        labels = { 'foo': 'bar' }
        new_relic = NewRelicStub()

        # preconditions
        self.assertEqual(len(new_relic.events), 0)

        # execute
        pipeline.load_as_events(
            self.logs(53),
            new_relic,
            labels,
            50,
            set(),
        )

        # verify
        self.assertEqual(len(new_relic.events), 2)
        l = new_relic.events[0]
        self.assertEqual(len(l), 50)
        l = new_relic.events[1]
        self.assertEqual(len(l), 3)

    def test_load_data_sends_logs_given_data_format_is_logs(self):
        '''
        load_data() sends log entries via the New Relic Logs API when the data format is set to DataFormat.LOGS
        given: an iterator over log entries
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a max rows value
        and given: a set of numeric field names
        when: load_data() is called
        and when: the data format is set to DataFormat.LOGS
        then: log entries are sent via the New Relic Logs API
        '''

        # setup
        labels = { 'foo': 'bar' }
        new_relic = NewRelicStub()

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)
        self.assertEqual(len(new_relic.events), 0)

        # execute
        pipeline.load_data(
            self.logs(),
            new_relic,
            DataFormat.LOGS,
            labels,
            50,
            set()
        )

        # verify
        self.assertEqual(len(new_relic.logs), 1)
        self.assertEqual(len(new_relic.events), 0)
        self.assertEqual(len(new_relic.logs[0]), 1)
        self.assertTrue('logs' in new_relic.logs[0][0])
        self.assertEqual(len(new_relic.logs[0][0]['logs']), 50)

    def test_load_data_sends_events_given_data_format_is_events(self):
        '''
        load_data() sends log entries via the New Relic Events API when the data format is set to DataFormat.EVENTS
        given: an iterator over log entries
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a max rows value
        and given: a set of numeric field names
        when: load_data() is called
        and when: the data format is set to DataFormat.EVENTS
        then: log entries are sent via the New Relic Events API
        '''

        # setup
        labels = { 'foo': 'bar' }
        new_relic = NewRelicStub()

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)
        self.assertEqual(len(new_relic.events), 0)

        # execute
        pipeline.load_data(
            self.logs(),
            new_relic,
            DataFormat.EVENTS,
            labels,
            50,
            set()
        )

        # verify
        self.assertEqual(len(new_relic.logs), 0)
        self.assertEqual(len(new_relic.events), 1)
        self.assertEqual(len(new_relic.events[0]), 50)

    def test_pipeline_init_given_no_max_rows(self):
        '''
        Pipeline.__init__() returns a new Pipeline with the default max_rows value
        given: an instance config
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        when: Pipeline.__init__() is called
        and when: no max_rows value is specified in the instance config
        and when: the data cache is None
        then: create a new Pipeline with the given values
        and: the default max_rows value
        '''

        # setup
        instance_config = mod_config.Config({})
        new_relic = NewRelicStub()
        labels = { 'foo': 'bar' }
        numeric_fields_list = set()

        # execute
        p = pipeline.Pipeline(
            instance_config,
            None,
            new_relic,
            DataFormat.LOGS,
            labels,
            numeric_fields_list,
        )

        # verify
        self.assertEqual(p.config, instance_config)
        self.assertIsNone(p.data_cache)
        self.assertEqual(p.new_relic, new_relic)
        self.assertEqual(p.data_format, DataFormat.LOGS)
        self.assertEqual(p.labels, labels)
        self.assertEqual(p.numeric_fields_list, numeric_fields_list)
        self.assertEqual(p.max_rows, pipeline.DEFAULT_MAX_ROWS)
        self.assertEqual(p.receivers, [])

    def test_pipeline_init_given_max_rows(self):
        '''
        Pipeline.__init__() returns a new Pipeline with the max_rows value specified in the given instance config
        given: an instance config
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        when: Pipeline.__init__() is called
        and when: a max_rows value is specified in the instance config
        and when: the max_rows value is less than MAX_ROWS
        and when: the data cache is None
        then: create a new Pipeline with the given values
        and: the given max_rows value
        '''

        # setup
        instance_config = mod_config.Config({
            'max_rows': 52,
        })
        new_relic = NewRelicStub()
        labels = { 'foo': 'bar' }
        numeric_fields_list = set()

        # execute
        p = pipeline.Pipeline(
            instance_config,
            None,
            new_relic,
            DataFormat.LOGS,
            labels,
            numeric_fields_list,
        )

        # verify
        self.assertEqual(p.config, instance_config)
        self.assertIsNone(p.data_cache)
        self.assertEqual(p.new_relic, new_relic)
        self.assertEqual(p.data_format, DataFormat.LOGS)
        self.assertEqual(p.labels, labels)
        self.assertEqual(p.numeric_fields_list, numeric_fields_list)
        self.assertEqual(p.max_rows, 52)
        self.assertEqual(p.receivers, [])

    def test_pipeline_init_given_max_rows_greater_than_limit(self):
        '''
        Pipeline.__init__() returns a new Pipeline with MAX_ROWS as the max_rows value, ignoring the value in the instance_config because it is over the maximum limit
        given: an instance config
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        when: Pipeline.__init__() is called
        and when: a max_rows value is specified in the instance config
        and when: the max_rows value is greater than MAX_ROWS
        and when: the data cache is None
        then: create a new Pipeline with the given values
        and: the given max_rows value is ignore and MAX_ROWS is used instead
        '''

        # setup
        instance_config = mod_config.Config({
            'max_rows': pipeline.MAX_ROWS + 1,
        })
        new_relic = NewRelicStub()
        labels = { 'foo': 'bar' }
        numeric_fields_list = set()

        # execute
        p = pipeline.Pipeline(
            instance_config,
            None,
            new_relic,
            DataFormat.LOGS,
            labels,
            numeric_fields_list,
        )

        # verify
        self.assertEqual(p.config, instance_config)
        self.assertIsNone(p.data_cache)
        self.assertEqual(p.new_relic, new_relic)
        self.assertEqual(p.data_format, DataFormat.LOGS)
        self.assertEqual(p.labels, labels)
        self.assertEqual(p.numeric_fields_list, numeric_fields_list)
        self.assertEqual(p.max_rows, pipeline.MAX_ROWS)
        self.assertEqual(p.receivers, [])

    def test_pipeline_add_receiver(self):
        '''
        Pipeline.add_receiver() adds a receiver to the pipeline
        given: an instance config
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        and given: a receiver
        when: Pipeline.add_receiver() is called
        then: the receiver is added to the receivers list
        '''

        # setup
        instance_config = mod_config.Config({})
        new_relic = NewRelicStub()
        labels = { 'foo': 'bar' }
        numeric_fields_list = set()
        receiver = ReceiverStub()

        # execute
        p = pipeline.Pipeline(
            instance_config,
            None,
            new_relic,
            DataFormat.LOGS,
            labels,
            numeric_fields_list,
        )
        p.add_receiver(receiver)

        # verify
        self.assertTrue(len(p.receivers) == 1)
        self.assertEqual(p.receivers[0], receiver)

    def test_pipeline_yield_all_executes_receivers_and_yields_all_results(self):
        '''
        Pipeline.yield_all() executes each receiver in turn and yields all the results in the order the receivers produce them
        given: an instance config
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        and given: there are two receivers
        and given: an http session
        when: Pipeline.yield_all() is called
        then: the receivers should be executed
        '''

        # setup
        instance_config = mod_config.Config({})
        new_relic = NewRelicStub()
        labels = { 'foo': 'bar' }
        numeric_fields_list = set()
        receiver1 = ReceiverStub(
            logs=[
                {
                    'message': 'receiver 1 log 1',
                    'attributes': { 'foo': 'bar' },
                },
                {
                    'message': 'receiver 1 log 2',
                    'attributes': { 'foo': 'bar' },
                },
            ]
        )
        receiver2 = ReceiverStub(
            logs=[
                {
                    'message': 'receiver 2 log 1',
                    'attributes': { 'beep': 'boop' },
                },
            ]
        )
        session = SessionStub()

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)

        # execute
        p = pipeline.Pipeline(
            instance_config,
            None,
            new_relic,
            DataFormat.LOGS,
            labels,
            numeric_fields_list,
        )
        p.add_receiver(receiver1)
        p.add_receiver(receiver2)

        iter = p.yield_all(session)
        logs = []

        for log in iter:
            logs.append(log)

        # verify
        self.assertTrue(len(p.receivers) == 2)
        self.assertEqual(p.receivers[0], receiver1)
        self.assertEqual(p.receivers[1], receiver2)
        self.assertTrue(receiver1.executed)
        self.assertTrue(receiver2.executed)
        self.assertEqual(len(logs), 3)
        l = logs[0]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'receiver 1 log 1')
        self.assertTrue('attributes' in l)
        self.assertTrue('foo' in l['attributes'])
        self.assertEqual(l['attributes']['foo'], 'bar')
        l = logs[1]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'receiver 1 log 2')
        self.assertTrue('attributes' in l)
        self.assertTrue('foo' in l['attributes'])
        self.assertEqual(l['attributes']['foo'], 'bar')
        l = logs[2]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'receiver 2 log 1')
        self.assertTrue('attributes' in l)
        self.assertTrue('beep' in l['attributes'])
        self.assertEqual(l['attributes']['beep'], 'boop')

    def test_pipeline_yield_all_raises_login_exception_if_receiver_does(self):
        '''
        Pipeline.yield_all() raises a LoginException if receiver.execute() does
        given: an instance config
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        and given: there are two receivers
        and given: an http session
        when: Pipeline.yield_all() is called
        and when: receiver.execute() raises a LoginException
        then: raise a LoginException
        '''

        # setup
        instance_config = mod_config.Config({})
        new_relic = NewRelicStub()
        labels = { 'foo': 'bar' }
        numeric_fields_list = set()
        receiver = ReceiverStub(raise_login_error=True)
        session = SessionStub()

        # execute / verify
        p = pipeline.Pipeline(
            instance_config,
            None,
            new_relic,
            DataFormat.LOGS,
            labels,
            numeric_fields_list,
        )
        p.add_receiver(receiver)

        with self.assertRaises(LoginException) as _:
            iter = p.yield_all(session)
            # Have to use next to cause the generator to execute the function
            # else get_log_file() won't get executed and our stub won't have
            # a chance to throw the fake exception.
            next(iter)

    def test_pipeline_yield_all_raises_salesforce_exception_if_receiver_does(self):
        '''
        Pipeline.yield_all() raises a SalesforceApiException if receiver.execute() does
        given: an instance config
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        and given: there are two receivers
        and given: an http session
        when: Pipeline.yield_all() is called
        and when: receiver.execute() raises a SalesforceApiException
        then: raise a SalesforceApiException
        '''

        # setup
        instance_config = mod_config.Config({})
        new_relic = NewRelicStub()
        labels = { 'foo': 'bar' }
        numeric_fields_list = set()
        receiver = ReceiverStub(raise_error=True)
        session = SessionStub()

        # execute / verify
        p = pipeline.Pipeline(
            instance_config,
            None,
            new_relic,
            DataFormat.LOGS,
            labels,
            numeric_fields_list,
        )
        p.add_receiver(receiver)

        with self.assertRaises(SalesforceApiException) as _:
            iter = p.yield_all(session)
            # Have to use next to cause the generator to execute the function
            # else get_log_file() won't get executed and our stub won't have
            # a chance to throw the fake exception.
            next(iter)

    def test_pipeline_execute_executes_receivers(self):
        '''
        Pipeline.execute() executes all receivers and sends data to New Relic
        given: an instance config
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        and given: there are two receivers
        and given: an http session
        when: Pipeline.execute() is called
        then: the receivers should be executed
        and: all receiver results are sent to New Relic
        '''

        # setup
        instance_config = mod_config.Config({})
        new_relic = NewRelicStub()
        labels = { 'foo': 'bar' }
        numeric_fields_list = set()
        receiver1 = ReceiverStub(
            logs=[
                {
                    'message': 'receiver 1 log 1',
                    'attributes': { 'foo': 'bar' },
                },
                {
                    'message': 'receiver 1 log 2',
                    'attributes': { 'foo': 'bar' },
                },
            ]
        )
        receiver2 = ReceiverStub(
            logs=[
                {
                    'message': 'receiver 2 log 1',
                    'attributes': { 'beep': 'boop' },
                },
            ]
        )
        session = SessionStub()

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)

        # execute
        p = pipeline.Pipeline(
            instance_config,
            None,
            new_relic,
            DataFormat.LOGS,
            labels,
            numeric_fields_list,
        )
        p.add_receiver(receiver1)
        p.add_receiver(receiver2)
        p.execute(session)

        # verify
        self.assertTrue(len(p.receivers) == 2)
        self.assertEqual(p.receivers[0], receiver1)
        self.assertEqual(p.receivers[1], receiver2)
        self.assertTrue(receiver1.executed)
        self.assertTrue(receiver2.executed)
        self.assertEqual(len(new_relic.logs), 1)
        self.assertEqual(len(new_relic.logs[0]), 1)
        self.assertTrue('logs' in new_relic.logs[0][0])
        self.assertEqual(len(new_relic.logs[0][0]['logs']), 3)
        logs = new_relic.logs[0][0]['logs']
        l = logs[0]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'receiver 1 log 1')
        self.assertTrue('attributes' in l)
        self.assertTrue('foo' in l['attributes'])
        self.assertEqual(l['attributes']['foo'], 'bar')
        l = logs[1]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'receiver 1 log 2')
        self.assertTrue('attributes' in l)
        self.assertTrue('foo' in l['attributes'])
        self.assertEqual(l['attributes']['foo'], 'bar')
        l = logs[2]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'receiver 2 log 1')
        self.assertTrue('attributes' in l)
        self.assertTrue('beep' in l['attributes'])
        self.assertEqual(l['attributes']['beep'], 'boop')

    def test_pipeline_execute_raises_login_exception_if_receiver_does(self):
        '''
        Pipeline.execute() raises a LoginException if receiver.execute() does
        given: an instance config
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        and given: there are two receivers
        and given: an http session
        when: Pipeline.execute() is called
        and when: receiver.execute() raises a LoginException
        then: raise a LoginException
        '''

        # setup
        instance_config = mod_config.Config({})
        new_relic = NewRelicStub()
        labels = { 'foo': 'bar' }
        numeric_fields_list = set()
        receiver = ReceiverStub(raise_login_error=True)
        session = SessionStub()

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)

        # execute / verify
        p = pipeline.Pipeline(
            instance_config,
            None,
            new_relic,
            DataFormat.LOGS,
            labels,
            numeric_fields_list,
        )
        p.add_receiver(receiver)

        with self.assertRaises(LoginException) as _:
            p.execute(session)

    def test_pipeline_execute_raises_salesforce_exception_if_receiver_does(self):
        '''
        Pipeline.execute() raises a SalesforceApiException if receiver.execute() does
        given: an instance config
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        and given: there are two receivers
        and given: an http session
        when: Pipeline.execute() is called
        and when: receiver.execute() raises a SalesforceApiException
        then: raise a SalesforceApiException
        '''

        # setup
        instance_config = mod_config.Config({})
        new_relic = NewRelicStub()
        labels = { 'foo': 'bar' }
        numeric_fields_list = set()
        receiver = ReceiverStub(raise_error=True)
        session = SessionStub()

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)

        # execute / verify
        p = pipeline.Pipeline(
            instance_config,
            None,
            new_relic,
            DataFormat.LOGS,
            labels,
            numeric_fields_list,
        )
        p.add_receiver(receiver)

        with self.assertRaises(SalesforceApiException) as _:
            p.execute(session)

    def test_pipeline_execute_raises_newrelic_exception_if_new_relic_post_logs_does(self):
        '''
        Pipeline.execute() raises a NewRelicApiException if new_relic.post_logs() does
        given: an instance config
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        and given: there are two receivers
        and given: an http session
        when: Pipeline.execute() is called
        and when: new_relic.post_logs() raises a NewRelicApiException
        then: raise a NewRelicApiException
        '''

        # setup
        instance_config = mod_config.Config({})
        new_relic = NewRelicStub(raise_error=True)
        labels = { 'foo': 'bar' }
        numeric_fields_list = set()
        receiver = ReceiverStub(
            logs=[
                {
                    'message': 'receiver 1 log 1',
                    'attributes': { 'foo': 'bar' },
                },
                {
                    'message': 'receiver 1 log 2',
                    'attributes': { 'foo': 'bar' },
                },
            ]
        )
        session = SessionStub()

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)

        # execute / verify
        p = pipeline.Pipeline(
            instance_config,
            None,
            new_relic,
            DataFormat.LOGS,
            labels,
            numeric_fields_list,
        )
        p.add_receiver(receiver)

        with self.assertRaises(NewRelicApiException) as _:
            p.execute(session)

    def test_pipeline_execute_raises_newrelic_exception_if_new_relic_post_events_does(self):
        '''
        Pipeline.execute() raises a NewRelicApiException if new_relic.post_events() does
        given: an instance config
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: a dict of key:value pairs to use as labels
        and given: a set of numeric field names
        and given: there are two receivers
        and given: an http session
        when: Pipeline.execute() is called
        and when: new_relic.post_events() raises a NewRelicApiException
        then: raise a NewRelicApiException
        '''

        # setup
        instance_config = mod_config.Config({})
        new_relic = NewRelicStub(raise_error=True)
        labels = { 'foo': 'bar' }
        numeric_fields_list = set()
        receiver = ReceiverStub(
            logs=[
                {
                    'message': 'receiver 1 log 1',
                    'attributes': { 'foo': 'bar' },
                },
                {
                    'message': 'receiver 1 log 2',
                    'attributes': { 'foo': 'bar' },
                },
            ]
        )
        session = SessionStub()

        # preconditions
        self.assertEqual(len(new_relic.logs), 0)

        # execute / verify
        p = pipeline.Pipeline(
            instance_config,
            None,
            new_relic,
            DataFormat.EVENTS,
            labels,
            numeric_fields_list,
        )
        p.add_receiver(receiver)

        with self.assertRaises(NewRelicApiException) as _:
            p.execute(session)

if __name__ == '__main__':
    unittest.main()
