import copy
from datetime import datetime
import json
import pytz
import unittest

from newrelic_logging import \
    config, \
    DataFormat, \
    pipeline, \
    util, \
    SalesforceApiException
from . import \
    DataCacheStub, \
    NewRelicStub, \
    QueryStub, \
    ResponseStub, \
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

    def test_init_fields_from_log_line(self):
        '''
        given: an event type, log line, and event fields mapping
        when: there is no matching mapping for the event type in the event
              fields mapping
        then: copy all fields in log line
        '''

        # setup
        log_line = {
            'foo': 'bar',
            'beep': 'boop',
        }

        # execute
        attrs = pipeline.init_fields_from_log_line('ApexCallout', log_line, {})

        # verify
        self.assertTrue(len(attrs) == 2)
        self.assertTrue(attrs['foo'] == 'bar')
        self.assertTrue(attrs['beep'] == 'boop')

        '''
        given: an event type, log line, and event fields mapping
        when: there is a matching mapping for the event type in the event
              fields mapping
        then: copy only the fields in the event fields mapping
        '''

        # execute
        attrs = pipeline.init_fields_from_log_line(
            'ApexCallout',
            log_line,
            { 'ApexCallout': ['foo'] }
        )

        # verify
        self.assertTrue(len(attrs) == 1)
        self.assertTrue(attrs['foo'] == 'bar')
        self.assertTrue(not 'beep' in attrs)

    def test_get_log_line_timestamp(self):
        '''
        given: a log line
        when: there is no TIMESTAMP attribute
        then: return the current timestamp
        '''

        # setup
        now = datetime.utcnow().replace(microsecond=0)

        # execute
        ts = pipeline.get_log_line_timestamp({})

        # verify
        self.assertEqual(now.timestamp(), ts)

        '''
        given: a log line
        when: there is a TIMESTAMP attribute
        then: parse the string in the format YYYYMMDDHHmmss.FFF and return
              the representative timestamp
        '''

        # setup
        epoch = now.strftime('%Y%m%d%H%M%S.%f')

        # execute
        ts1 = pytz.utc.localize(now).replace(microsecond=0).timestamp()
        ts2 = pipeline.get_log_line_timestamp({ 'TIMESTAMP': epoch })

        # verify
        self.assertEqual(ts1, ts2)

    def test_pack_log_line_into_log(self):
        '''
        given: a query object, record ID, event type, log line, line number,
               and event fields mapping
        when: there is a TIMESTAMP and EVENT_TYPE field, no query options, and
              no matching event mapping
        then: return a log entry with the message "LogFile $ID row $LINENO",
              and attributes dict containing all fields from the log line,
              an EVENT_TYPE field with the log line event type, a TIMESTAMP
              field with the log line timestamp, and a timestamp field with
              the timestamp epoch value
        '''

        # setup
        query = QueryStub({})

        # execute
        log = pipeline.pack_log_line_into_log(
            query,
            '00001111AAAABBBB',
            'ApexCallout',
            self.log_lines[0],
            0,
            {},
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertEqual(log['message'], 'LogFile 00001111AAAABBBB row 0')

        attrs = log['attributes']
        self.assertEqual(attrs['EVENT_TYPE'], 'ApexCallout')
        self.assertEqual(attrs['LogFileId'], '00001111AAAABBBB')
        self.assertTrue('timestamp' in attrs)
        ts = pipeline.get_log_line_timestamp({
            'TIMESTAMP': '20240311160000.000'
        })
        self.assertEqual(int(ts), attrs['timestamp'])
        self.assertTrue('REQUEST_ID' in attrs)
        self.assertTrue('RUN_TIME' in attrs)
        self.assertTrue('CPU_TIME' in attrs)
        self.assertEqual('YYZ:abcdef123456', attrs['REQUEST_ID'])
        self.assertEqual('2112', attrs['RUN_TIME'])
        self.assertEqual('10', attrs['CPU_TIME'])

        '''
        given: a query object, record ID, event type, log line, line number,
               and event fields mapping
        when: there is a TIMESTAMP and EVENT_TYPE field, no matching event
              mapping, and the event_type and rename_timestamp query options
        then: return the same as case 1 but with the event type specified
              in the query options, the epoch value in the field specified
              in the query options and no timestamp field
        '''

        # setup
        query = QueryStub({
            'event_type': 'CustomSFEvent',
            'rename_timestamp': 'custom_timestamp',
        })

        # execute
        log = pipeline.pack_log_line_into_log(
            query,
            '00001111AAAABBBB',
            'ApexCallout',
            self.log_lines[0],
            0,
            {},
        )

        # verify
        attrs = log['attributes']
        self.assertTrue('custom_timestamp' in attrs)
        self.assertEqual(attrs['EVENT_TYPE'], 'CustomSFEvent')
        self.assertEqual(attrs['custom_timestamp'], int(ts))
        self.assertTrue(not 'timestamp' in log)

    def test_export_log_lines(self):
        '''
        given: an http session, url, access token, and chunk size
        when: the response produces a non-200 status code
        then: raise a SalesforceApiException
        '''

        # setup
        session = SessionStub()
        session.response = ResponseStub(500, 'Error', '', [])

        # execute/verify
        with self.assertRaises(SalesforceApiException):
            pipeline.export_log_lines(session, '', '', 100)

        '''
        given: an http session, url, access token, and chunk size
        when: the response produces a 200 status code
        then: return a generator iterator that yields one line of data at a time
        '''

        # setup
        session.response = ResponseStub(200, 'OK', '', self.log_rows)

        #execute
        response = pipeline.export_log_lines(session, '', '', 100)

        lines = []
        for line in response:
            lines.append(line)

        # verify
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], self.log_rows[0])
        self.assertEqual(lines[1], self.log_rows[1])
        self.assertEqual(lines[2], self.log_rows[2])

    def test_transform_log_lines(self):
        '''
        given: an iterable of log rows, query, record id, event type, event
               types mapping and no data cache
        when: the response produces a 200 status code
        then: return a generator iterator that yields one New Relic log
              object for each row except the header row
        '''

        # execute
        logs = pipeline.transform_log_lines(
            self.log_rows,
            QueryStub({}),
            '00001111AAAABBBB',
            'ApexCallout',
            None,
            {},
        )

        l = []

        for log in logs:
            l.append(log)

        # verify
        self.assertEqual(len(l), 2)
        self.assertTrue('message' in l[0])
        self.assertTrue('attributes' in l[0])
        self.assertEqual(l[0]['message'], 'LogFile 00001111AAAABBBB row 0')
        attrs = l[0]['attributes']
        self.assertTrue('EVENT_TYPE' in attrs)
        self.assertTrue('timestamp' in attrs)
        self.assertEqual(1710172800, attrs['timestamp'])

        self.assertTrue('message' in l[1])
        self.assertTrue('attributes', l[1])
        self.assertEqual(l[1]['message'], 'LogFile 00001111AAAABBBB row 1')
        attrs = l[1]['attributes']
        self.assertTrue('EVENT_TYPE' in attrs)
        self.assertTrue('timestamp' in attrs)
        self.assertEqual(1710176400, attrs['timestamp'])

        '''
        given: an iterable of log rows, query, record id, event type, event
               types mapping and a data cache
        when: the data cache contains the REQUEST_ID for some of the log lines
        then: return a generator iterator that yields one New Relic log
              object for each row with a REQUEST_ID
        '''

        # execute
        logs = pipeline.transform_log_lines(
            self.log_rows,
            QueryStub({}),
            '00001111AAAABBBB',
            'ApexCallout',
            DataCacheStub(cached_logs={
                '00001111AAAABBBB': [ 'YYZ:abcdef123456' ]
            }),
            {},
        )

        l = []

        for log in logs:
            l.append(log)

        # verify
        self.assertEqual(len(l), 1)
        self.assertEqual(
            l[0]['attributes']['REQUEST_ID'],
            'YYZ:fedcba654321'
        )


    def test_pack_event_record_into_log(self):
        created_date = self.event_records[0]['CreatedDate']
        timestamp = util.get_timestamp(created_date)

        base_expected_attrs = {
            'Id': '00001111AAAABBBB',
            'Name': 'My Account',
            'BillingCity': None,
            'CreatedDate': created_date,
            'CreatedBy.Name': 'Foo Bar',
            'CreatedBy.Profile.Name': 'Beep Boop',
            'CreatedBy.UserType': 'Bip Bop',
            'EVENT_TYPE': 'Account',
            'timestamp': timestamp,
        }

        '''
        given: a query, record id and event record
        when: there are no query options, the record id is not None, and the
              event record contains a 'type' field in the 'attributes' field
        then: return a log with the 'message' attribute set to the event type
              specified in the record's 'attributes.type' field + the created
              date; where the 'attributes' attribute contains all attributes
              according to process_query_result, an 'Id' attribute set to the
              passed record ID, an 'EVENT_TYPE' attribute set to the event type
              specified in the record's 'attributes.type' field, and a
              'timestamp' attribute set to the epoch value representing the
              record's 'CreatedDate' field; and with the 'timestamp' attribute
              also set to the epoch value representing the record's
              'CreatedDate' field.
        '''

        # setup
        query = QueryStub({})

        # execute
        log = pipeline.pack_event_record_into_log(
            query,
            '00001111AAAABBBB',
            self.event_records[0]
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'Account {created_date}')
        self.assertEqual(log['attributes'], base_expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

        '''
        given: a query, record id, and an event record
        when: there are no query options, the record id is None, and the
              event record contains a 'type' field in the 'attributes' field
        then: return a log as in use case 1 but with the 'Id' value in the
              log 'attributes' attribute set to the 'Id' value from the event
              record
        '''

        # setup
        event_record = copy.deepcopy(self.event_records[0])
        expected_attrs = copy.deepcopy(base_expected_attrs)
        expected_attrs['Id'] = '000012345'

        # execute
        log = pipeline.pack_event_record_into_log(
            query,
            None,
            event_record
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'Account {created_date}')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

        '''
        given: a query, record id, and an event record
        when: the 'event_type' query option is specified, the record id is not
              None, and the event record contains a 'type' field in the
              'attributes' field
        then: return a log as in use case 1 but with the event type in the log
              'message' attribute set to the custom event type specified in the
              'event_type' query option plus the created date, and with the
              'EVENT_TYPE' attribute in the log 'attributes' attribute set to
              the custom event type
        '''

        # setup
        event_record = copy.deepcopy(self.event_records[0])
        expected_attrs = copy.deepcopy(base_expected_attrs)
        expected_attrs['EVENT_TYPE'] = 'CustomEvent'

        # execute
        log = pipeline.pack_event_record_into_log(
            QueryStub({ 'event_type': 'CustomEvent' }),
            '00001111AAAABBBB',
            event_record
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'CustomEvent {created_date}')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

        '''
        given: a query, record id, and an event record
        when: there are no query options, the record id is not None, and the
              event record does not contain an 'attributes' field
        then: return a log as in use case 1 but with the event type in the log
              'message' attribute set to the default event type plus the created
              date, and with no 'EVENT_TYPE' attribute in the log 'attributes'
              attribute
        '''

        # setup
        event_record = copy.deepcopy(self.event_records[0])
        event_record.pop('attributes')
        expected_attrs = copy.deepcopy(base_expected_attrs)
        expected_attrs.pop('EVENT_TYPE')

        # execute
        log = pipeline.pack_event_record_into_log(
            query,
            '00001111AAAABBBB',
            event_record
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'SFEvent {created_date}')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

        '''
        given: a query, record id, and an event record
        when: there are no query options, the record id is not None, and the
              event record does contain an 'attributes' field but it is not a
              dictionary
        then: return a log as in the previous use case
        '''

        # setup
        event_record = copy.deepcopy(self.event_records[0])
        event_record['attributes'] = 'test'
        expected_attrs = copy.deepcopy(base_expected_attrs)
        expected_attrs.pop('EVENT_TYPE')

        # execute
        log = pipeline.pack_event_record_into_log(
            query,
            '00001111AAAABBBB',
            event_record
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'SFEvent {created_date}')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

        '''
        given: a query, record id, and an event record
        when: there are no query options, the record id is not None, and the
              event record does not contain a 'type' field in the 'attributes'
              field
        then: return a log as in the previous use case
        '''

        # setup
        event_record = copy.deepcopy(self.event_records[0])
        event_record['attributes'].pop('type')
        expected_attrs = copy.deepcopy(base_expected_attrs)
        expected_attrs.pop('EVENT_TYPE')

        # execute
        log = pipeline.pack_event_record_into_log(
            query,
            '00001111AAAABBBB',
            event_record
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'SFEvent {created_date}')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

        '''
        given: a query, record id, and an event record
        when: there are no query options, the record id is not None, and the
              event record does contain a 'type' field in the 'attributes'
              field but it is not a string
        then: return a log as in the previous use case
        '''

        # setup
        event_record = copy.deepcopy(self.event_records[0])
        event_record['attributes']['type'] = 12345
        expected_attrs = copy.deepcopy(base_expected_attrs)
        expected_attrs.pop('EVENT_TYPE')

        # execute
        log = pipeline.pack_event_record_into_log(
            query,
            '00001111AAAABBBB',
            event_record
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'SFEvent {created_date}')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

        '''
        given: a query, record id, and an event record
        when: the 'timestamp_attr' query option is specified, the field
              specified in the 'timestamp_attr' query option exists in the event
              record, the record id is not None, and the event record contains a
              'type' field in the 'attributes' field
        then: return a log as in use case 1 but using the timestamp from the
              field specified in the 'timestamp_attr' query option.
        '''

        # setup
        __now = datetime.now()

        def _now():
            nonlocal __now
            return __now

        util._NOW = _now

        created_date_2 = self.event_records[1]['CreatedDate']
        timestamp = util.get_timestamp(created_date_2)

        event_record = copy.deepcopy(self.event_records[0])
        event_record['CustomDate'] = created_date_2
        expected_attrs = copy.deepcopy(base_expected_attrs)
        expected_attrs['CustomDate'] = created_date_2
        expected_attrs['timestamp'] = timestamp

        # execute
        log = pipeline.pack_event_record_into_log(
            QueryStub({ 'timestamp_attr': 'CustomDate' }),
            '00001111AAAABBBB',
            event_record
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'Account {created_date_2}')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

        '''
        given: a query, record id, and an event record
        when: the 'timestamp_attr' query option is specified but the specified
              attribute name is not in the event record, the record id is not
              None, and the event record contains a 'type' field in the
              'attributes' field
        then: return a log as in use case 1 but the log 'message' attribute does
              not contain a date, the 'timestamp' attribute of the log
              'attributes' attribute is set to the current time, and with the
              log 'timestamp' attribute set to the current time.
        '''

        # setup
        event_record = copy.deepcopy(self.event_records[0])
        expected_attrs = copy.deepcopy(base_expected_attrs)
        timestamp = util.get_timestamp()
        expected_attrs['timestamp'] = timestamp

        # execute
        log = pipeline.pack_event_record_into_log(
            QueryStub({ 'timestamp_attr': 'NotPresent' }),
            '00001111AAAABBBB',
            event_record
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'Account')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

        '''
        given: a query, record id, and an event record
        when: no query options are specified, the record id is not None, and the
              event record does not contain a 'CreatedDate' field
        then: return the same as the previous use case
        '''

        # setup
        event_record = copy.deepcopy(self.event_records[0])
        event_record.pop('CreatedDate')
        expected_attrs = copy.deepcopy(base_expected_attrs)
        expected_attrs.pop('CreatedDate')
        timestamp = util.get_timestamp()
        expected_attrs['timestamp'] = timestamp

        # execute
        log = pipeline.pack_event_record_into_log(
            query,
            '00001111AAAABBBB',
            event_record
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'Account')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

        '''
        given: a query, record id, and an event record
        when: the 'rename_timestamp' query option is specified, the record id is
              not None, and the event record contains a 'type' field in the
              'attributes' field
        then: return the same as use case 1 but with an attribute with the name
              specified in the 'rename_timestamp' query option set to the
              created date in the log 'attributes' attribute, no 'timestamp'
              attribute in the log 'attributes' attribute, and with no log
              'timestamp' attribute
        '''

        # setup
        event_record = copy.deepcopy(self.event_records[0])
        expected_attrs = copy.deepcopy(base_expected_attrs)
        timestamp = util.get_timestamp(created_date)
        expected_attrs['custom_timestamp'] = timestamp
        expected_attrs.pop('timestamp')

        # execute
        log = pipeline.pack_event_record_into_log(
            QueryStub({ 'rename_timestamp': 'custom_timestamp' }),
            '00001111AAAABBBB',
            event_record
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue(not 'timestamp' in log)
        self.assertEqual(log['message'], f'Account {created_date}')
        self.assertEqual(log['attributes'], expected_attrs)

    def test_transform_event_records(self):
        '''
        given: an event record, query, and no data cache
        when: the record contains an 'Id' field
        then: return a log with the 'Id' attribute in the log 'attributes' set
              to the value of the 'Id' attribute
        when: the record does not contain an 'Id' field and the 'id' query
              option is not set
        then: return a log with no 'Id' attribute in the log 'attributes' field
        '''

        # execute
        logs = pipeline.transform_event_records(
            self.event_records,
            QueryStub({}),
            None,
        )

        l = []

        for log in logs:
            l.append(log)

        # verify
        self.assertEqual(len(l), 3)
        self.assertTrue('Id' in l[0]['attributes'])
        self.assertTrue('Id' in l[1]['attributes'])
        self.assertEqual(l[0]['attributes']['Id'], '000012345')
        self.assertEqual(l[1]['attributes']['Id'], '000054321')
        self.assertTrue(not 'Id' in l[2]['attributes'])

        '''
        given: an event record, query, and no data cache
        when: the record does not contain an 'Id' field, the 'id' query option
              is set and the record contains the field set in the 'id' query
              option
        then: return a log with a generated id
        '''

        # execute
        logs = pipeline.transform_event_records(
            self.event_records[2:],
            QueryStub({ 'id': ['Name'] }),
            None,
        )

        l = []

        for log in logs:
            l.append(log)

        # verify
        customId = util.generate_record_id([ 'Name' ], self.event_records[2])
        self.assertTrue('Id' in l[0]['attributes'])
        self.assertEqual(l[0]['attributes']['Id'], customId)

        '''
        given: an event record, query, and a data cache
        when: the data cache contains cached record IDs
        then: return only logs with record ids that do not match those in the
              cache
        '''

        # execute
        logs = pipeline.transform_event_records(
            self.event_records,
            QueryStub({}),
            DataCacheStub(
                cached_logs={},
                cached_events=[ '000012345', '000054321' ]
            ),
        )

        l = []

        for log in logs:
            l.append(log)

        # verify
        self.assertEqual(len(l), 1)
        self.assertEqual(
            l[0]['attributes']['Name'],
            'My Last Account',
        )

    def test_load_as_logs(self):
        def logs(n = 50):
            for i in range(0, n):
                yield {
                    'message': f'log {i}',
                    'attributes': {
                        'EVENT_TYPE': f'SFEvent{i}',
                        'REQUEST_ID': f'abcdef-{i}',
                    },
                }

        '''
        given: an generator iterator of logs, newrelic instance, set of labels,
               and a max rows value
        when: their are less than the maximum number of rows, n
        then: a single Logs API post should be made with a 'common' property
              that contains all the labels and a 'logs' property that contains
              n log entries
        '''

        # setup
        labels = { 'foo': 'bar' }
        newrelic = NewRelicStub()

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)

        # execute
        pipeline.load_as_logs(
            logs(),
            newrelic,
            labels,
            pipeline.DEFAULT_MAX_ROWS,
        )

        # verify
        self.assertEqual(len(newrelic.logs), 1)
        l = newrelic.logs[0]
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

        '''
        given: an generator iterator of logs, newrelic instance, set of labels,
               and a max rows value
        when: their are more than the maximum number of rows, n
        then: floor(n / max) Logs API posts should be made each containing max
              logs in the 'logs' property and a 'common' property that contains
              all the labels. IFF n % max > 0, an additional Logs API post is
              made containing n % max logs in the 'logs' property and a 'common'
              property that contains all the labels.
        '''

        # setup
        newrelic = NewRelicStub()

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)

        # execute
        pipeline.load_as_logs(
            logs(150),
            newrelic,
            labels,
            50,
        )

        # verify
        self.assertEqual(len(newrelic.logs), 3)
        for i in range(0, 3):
            l = newrelic.logs[i]
            self.assertEqual(len(l), 1)
            l = l[0]
            self.assertTrue('logs' in l)
            self.assertTrue('common' in l)
            self.assertEqual(len(l['logs']), 50)

        # setup
        newrelic = NewRelicStub()

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)

        # execute
        pipeline.load_as_logs(
            logs(53),
            newrelic,
            labels,
            50,
        )

        # verify
        self.assertEqual(len(newrelic.logs), 2)
        l = newrelic.logs[0]
        self.assertEqual(len(l), 1)
        l = l[0]
        self.assertTrue('logs' in l)
        self.assertTrue('common' in l)
        self.assertEqual(len(l['logs']), 50)
        l = newrelic.logs[1]
        self.assertEqual(len(l), 1)
        l = l[0]
        self.assertTrue('logs' in l)
        self.assertTrue('common' in l)
        self.assertEqual(len(l['logs']), 3)

    def test_pack_log_into_event(self):
        '''
        given: a single log, set of labels, and a set of numeric field names
        when: the set of numeric field names is the empty set and the log
              contains an 'EVENT_TYPE' property
        then: return a single event with a property for each attribute specified
              in the 'attributes' field of the log, a property for each label,
              and an 'eventType' property set to the value of the 'EVENT_TYPE'
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

        '''
        given: a single log, set of labels, and a set of numeric field names
        when: the set of numeric field names is not empty
        then: return the same as use case 1 except each property in the returned
              event matching a property in the numeric field names set is
              converted to a number and non-numeric values are left as is.
        '''

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

        '''
        given: a single log, set of labels, and a set of numeric field names
        when: the set of numeric field names is the empty set and the log
              does not contain an 'EVENT_TYPE' property
        then: return the same as use case 1 except the 'eventType' attribute is
              set to the default event name.
        '''

        # setup
        log_lines = copy.deepcopy(self.log_lines)

        del log_lines[0]['EVENT_TYPE']

        log['attributes'] = log_lines[0]

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

    def test_load_as_events(self):
        def logs(n = 50):
            for i in range(0, n):
                yield {
                    'message': f'log {i}',
                    'attributes': {
                        'EVENT_TYPE': f'SFEvent{i}',
                        'REQUEST_ID': f'abcdef-{i}',
                    },
                }

        '''
        given: an generator iterator of logs, newrelic instance, set of labels,
               max rows value, and a set of numeric field names
        when: their are less than the maximum number of rows, n
        then: a single Events API post should be made with n events
        '''

        # setup
        labels = { 'foo': 'bar' }
        newrelic = NewRelicStub()

        # preconditions
        self.assertEqual(len(newrelic.events), 0)

        # execute
        pipeline.load_as_events(
            logs(),
            newrelic,
            labels,
            pipeline.DEFAULT_MAX_ROWS,
            set(),
        )

        # verify
        self.assertEqual(len(newrelic.events), 1)
        l = newrelic.events[0]
        self.assertEqual(len(l), 50)
        for i, event in enumerate(l):
            self.assertTrue('foo' in event)
            self.assertEqual(event['foo'], 'bar')
            self.assertTrue('EVENT_TYPE' in event)
            self.assertEqual(event['EVENT_TYPE'], f'SFEvent{i}')
            self.assertTrue('REQUEST_ID' in event)
            self.assertEqual(event['REQUEST_ID'], f'abcdef-{i}')

        '''
        given: an generator iterator of logs, newrelic instance, set of labels,
               max rows value, and a set of numeric field names
        when: their are more than the maximum number of rows, n
        then: floor(n / max) Events API posts should be made each containing max
              events. IFF n % max > 0, an additional Events API post is made
              containing n % max events.
        '''

        # setup
        newrelic = NewRelicStub()

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)

        # execute
        pipeline.load_as_events(
            logs(150),
            newrelic,
            labels,
            50,
            set(),
        )

        # verify
        self.assertEqual(len(newrelic.events), 3)
        for i in range(0, 3):
            l = newrelic.events[i]
            self.assertEqual(len(l), 50)

        # setup
        newrelic = NewRelicStub()

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)

        # execute
        pipeline.load_as_events(
            logs(53),
            newrelic,
            labels,
            50,
            set(),
        )

        # verify
        self.assertEqual(len(newrelic.events), 2)
        l = newrelic.events[0]
        self.assertEqual(len(l), 50)
        l = newrelic.events[1]
        self.assertEqual(len(l), 3)

    def test_load_data(self):
        def logs(n = 50):
            for i in range(0, n):
                yield {
                    'message': f'log {i}',
                    'attributes': {
                        'EVENT_TYPE': f'SFEvent{i}',
                        'REQUEST_ID': f'abcdef-{i}',
                    },
                }

        '''
        given: a generator iterator of logs, newrelic instance, data format,
               set of labels, max rows value, and a set of numeric field names
        when: the data format is set to DataFormat.LOGS
        then: log data is sent via the New Relic Logs API.
        '''

        # setup
        newrelic = NewRelicStub()

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)
        self.assertEqual(len(newrelic.events), 0)

        # execute
        pipeline.load_data(
            logs(),
            newrelic,
            DataFormat.LOGS,
            { 'foo': 'bar' },
            50,
            set()
        )

        # verify
        self.assertEqual(len(newrelic.logs), 1)
        self.assertEqual(len(newrelic.events), 0)
        self.assertEqual(len(newrelic.logs[0]), 1)
        self.assertTrue('logs' in newrelic.logs[0][0])
        self.assertEqual(len(newrelic.logs[0][0]['logs']), 50)

        '''
        given: a generator iterator of logs, newrelic instance, data format,
               set of labels, max rows value, and a set of numeric field names
        when: the data format is set to DataFormat.EVENTS
        then: log data is sent via the New Relic Events API.
        '''

        # setup
        newrelic = NewRelicStub()

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)
        self.assertEqual(len(newrelic.events), 0)

        # execute
        pipeline.load_data(
            logs(),
            newrelic,
            DataFormat.EVENTS,
            { 'foo': 'bar' },
            50,
            set()
        )

        # verify
        self.assertEqual(len(newrelic.logs), 0)
        self.assertEqual(len(newrelic.events), 1)
        self.assertEqual(len(newrelic.events[0]), 50)

    def test_pipeline_process_log_record(self):
        '''
        given: an instance configuration, data cache, http session, newrelic
               instance, data format, set of labels, event type fields mapping,
               set of numeric field names, query, instance url, access token and
               log record
        when: the pipeline is configured with the configuration, session,
              newrelic instance, data format, labels, event type fields mapping,
              and numeric field names
        and when: the data format is set to DataFormat.LOGS
        and when: a log record is being processed
        and when: the number of log lines to be processed is less than the
                  maximum number of rows
        and when: no data cache is specified
        then: a single Logs API post is made containing all labels in the
              'common' property of the logs post and one log for each exported
              and transformed log line with the correct attributes from the
              corresponding log line using the record ID, event type, and file
              name from the given record
        '''

        # setup
        cfg = config.Config({})
        session = SessionStub()
        session.response = ResponseStub(200, 'OK', '', self.log_rows)
        newrelic = NewRelicStub()
        query = QueryStub({})

        p = pipeline.Pipeline(
            cfg,
            None,
            newrelic,
            DataFormat.LOGS,
            { 'foo': 'bar' },
            {},
            set(),
        )

        record = self.log_records[0]

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)

        # execute
        p.process_log_record(
            session,
            query,
            'https://test.local.test',
            '12345',
            record,
        )

        # verify
        self.assertEqual(len(newrelic.logs), 1)
        l = newrelic.logs[0]
        self.assertEqual(len(l), 1)
        l = l[0]
        self.assertTrue('logs' in l)
        self.assertTrue('common' in l)
        self.assertTrue(type(l['common']) is dict)
        self.assertTrue('foo' in l['common'])
        self.assertEqual(l['common']['foo'], 'bar')
        self.assertEqual(len(l['logs']), 2)

        logs = l['logs']
        log0 = logs[0]
        log1 = logs[1]

        self.assertTrue('message' in log0)
        self.assertEqual(log0['message'], 'LogFile 00001111AAAABBBB row 0')
        self.assertTrue('attributes' in log0)
        self.assertTrue('EVENT_TYPE' in log0['attributes'])
        self.assertEqual(log0['attributes']['EVENT_TYPE'], f'ApexCallout')
        self.assertTrue('REQUEST_ID' in log0['attributes'])
        self.assertEqual(log0['attributes']['REQUEST_ID'], f'YYZ:abcdef123456')

        self.assertTrue('message' in log1)
        self.assertEqual(log1['message'], 'LogFile 00001111AAAABBBB row 1')
        self.assertTrue('attributes' in log1)
        self.assertTrue('EVENT_TYPE' in log1['attributes'])
        self.assertEqual(log1['attributes']['EVENT_TYPE'], f'ApexCallout')
        self.assertTrue('REQUEST_ID' in log0['attributes'])
        self.assertEqual(log1['attributes']['REQUEST_ID'], f'YYZ:fedcba654321')

        '''
        given: the values from use case 1
        when: the pipeline is configured as in use case 1
        and when: the data format is set to DataFormat.LOGS
        and when: the number of log lines to be processed is less than the
                  maximum number of rows,
        and when: a data cache is specified
        and when: the record ID matches a record ID in the data cache
        then: no log entries are sent
        '''

        # setup
        data_cache = DataCacheStub(skip_record_ids=['00001111AAAABBBB'])
        newrelic = NewRelicStub()

        p = pipeline.Pipeline(
            cfg,
            data_cache,
            newrelic,
            DataFormat.LOGS,
            { 'foo': 'bar' },
            {},
            set(),
        )

        record = self.log_records[0]

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)

        # execute
        p.process_log_record(
            session,
            query,
            'https://test.local.test',
            '12345',
            record,
        )

        # verify
        self.assertEqual(len(newrelic.logs), 0)

        '''
        given: the values from use case 2
        when: the pipeline is configured as in use case 2
        and when: the data format is set to DataFormat.LOGS
        and when: the number of log lines to be processed is less than the
                  maximum number of rows,
        and when: a data cache is specified
        and when: the record ID matches a record ID in the data cache
        and when: the 'Interval' value of the record is set to 'Daily'
        then: A Logs API post is made for the record anyway
        '''

        # setup
        newrelic = NewRelicStub()

        p = pipeline.Pipeline(
            cfg,
            data_cache,
            newrelic,
            DataFormat.LOGS,
            { 'foo': 'bar' },
            {},
            set(),
        )

        new_record = copy.deepcopy(record)
        new_record['Interval'] = 'Daily'

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)

        # execute
        p.process_log_record(
            session,
            query,
            'https://test.local.test',
            '12345',
            new_record,
        )

        # verify
        self.assertEqual(len(newrelic.logs), 1)
        l = newrelic.logs[0]
        self.assertEqual(len(l), 1)
        l = l[0]
        self.assertTrue('logs' in l)
        self.assertTrue('common' in l)
        self.assertTrue(type(l['common']) is dict)
        self.assertTrue('foo' in l['common'])
        self.assertEqual(l['common']['foo'], 'bar')
        self.assertEqual(len(l['logs']), 2)

        '''
        given: the values from use case 3
        when: the pipeline is configured as in use case 3
        and when: the data format is set to DataFormat.LOGS
        and when: the number of log lines to be processed is less than the
                  maximum number of rows,
        and when: a data cache is specified
        and when: the cache contains a list of log line IDs for the record ID
        then: A Logs API post is made for the record containing log entries only
              for log lines that have log line IDs that are not in the list of
              cached log lines for the record ID
        '''

        # setup
        data_cache = DataCacheStub(
            cached_logs={
                '00001111AAAABBBB': ['YYZ:abcdef123456', 'YYZ:fedcba654321']
            }
        )
        newrelic = NewRelicStub()

        p = pipeline.Pipeline(
            cfg,
            data_cache,
            newrelic,
            DataFormat.LOGS,
            { 'foo': 'bar' },
            {},
            set(),
        )

        record = self.log_records[0]

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)

        # execute
        p.process_log_record(
            session,
            query,
            'https://test.local.test',
            '12345',
            record,
        )

        # verify
        self.assertEqual(len(newrelic.logs), 0)

    def test_pipeline_process_event_records(self):
        '''
        given: an instance configuration, data cache, http session, newrelic
               instance, data format, set of labels, event type fields mapping,
               set of numeric field names, query, and a set of event records
        when: the pipeline is configured with the configuration, session,
              newrelic instance, data format, labels, event type fields mapping,
              and numeric field names
        and when: the data format is set to DataFormat.LOGS
        and when: event records are being processed
        and when: the number of event records to be processed is less than the
                  maximum number of rows
        and when: no data cache is specified
        then: a single Events API post is made containing all labels in the
              'common' property of the logs post and one log for each exported
              and transformed event record with the correct attributes from the
              corresponding event record
        '''

        # setup
        cfg = config.Config({})
        newrelic = NewRelicStub()
        query = QueryStub({ 'id': ['Name'] })

        p = pipeline.Pipeline(
            cfg,
            None,
            newrelic,
            DataFormat.LOGS,
            { 'foo': 'bar' },
            {},
            set(),
        )

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)

        # execute
        p.process_event_records(query, self.event_records)

        # verify
        self.assertEqual(len(newrelic.logs), 1)
        l = newrelic.logs[0]
        self.assertEqual(len(l), 1)
        l = l[0]
        self.assertTrue('logs' in l)
        self.assertTrue('common' in l)
        self.assertTrue(type(l['common']) is dict)
        self.assertTrue('foo' in l['common'])
        self.assertEqual(l['common']['foo'], 'bar')
        self.assertEqual(len(l['logs']), 3)

        logs = l['logs']
        log0 = logs[0]
        log1 = logs[1]
        log2 = logs[2]

        self.assertTrue('message' in log0)
        self.assertEqual(log0['message'], 'Account 2024-03-11T00:00:00.000+0000')
        self.assertTrue('attributes' in log0)
        self.assertTrue('Id' in log0['attributes'])
        self.assertEqual(log0['attributes']['Id'], f'000012345')
        self.assertTrue('Name' in log0['attributes'])
        self.assertEqual(log0['attributes']['Name'], f'My Account')

        self.assertTrue('message' in log1)
        self.assertEqual(log1['message'], 'Account 2024-03-10T00:00:00.000+0000')
        self.assertTrue('attributes' in log1)
        self.assertTrue('Id' in log1['attributes'])
        self.assertEqual(log1['attributes']['Id'], f'000054321')
        self.assertTrue('Name' in log1['attributes'])
        self.assertEqual(log1['attributes']['Name'], f'My Other Account')

        customId = util.generate_record_id([ 'Name' ], self.event_records[2])

        self.assertTrue('message' in log2)
        self.assertEqual(log2['message'], 'Account 2024-03-09T00:00:00.000+0000')
        self.assertTrue('attributes' in log2)
        self.assertTrue('Id' in log2['attributes'])
        self.assertEqual(log2['attributes']['Id'], customId)
        self.assertTrue('Name' in log2['attributes'])
        self.assertEqual(log2['attributes']['Name'], f'My Last Account')

    def test_pipeline_execute(self):
        '''
        given: an instance configuration, data cache, http session, newrelic
               instance, data format, set of labels, event type fields mapping,
               set of numeric field names, query, and a set of query result
               records
        when: the pipeline is configured with the configuration, session,
              newrelic instance, data format, labels, event type fields mapping,
              and numeric field names
        and when: the first record in the result set contains a 'LogFile'
                  attribute
        and when: the number of log lines to be processed is less than the
                  maximum number of rows
        and when: a data cache is specified
        then: a single Logs API post is made containing all labels in the
              'common' property of the logs post and one log for each exported
              and transformed log line, and the cache is flushed
        '''

        # setup
        cfg = config.Config({})
        session = SessionStub()
        session.response = ResponseStub(200, 'OK', '', self.log_rows)
        newrelic = NewRelicStub()
        query = QueryStub({})
        data_cache = DataCacheStub()

        p = pipeline.Pipeline(
            cfg,
            data_cache,
            newrelic,
            DataFormat.LOGS,
            { 'foo': 'bar' },
            {},
            set(),
        )

        # preconditions
        self.assertEqual(len(newrelic.logs), 0)

        # execute
        p.execute(
            session,
            query,
            'https://test.local.test',
            '12345',
            self.log_records,
        )

        # verify
        self.assertEqual(len(newrelic.logs), 2)

        for _, l in enumerate(newrelic.logs):
            self.assertEqual(len(l), 1)
            l = l[0]
            self.assertTrue('logs' in l)
            self.assertTrue('common' in l)
            self.assertTrue(type(l['common']) is dict)
            self.assertTrue('foo' in l['common'])
            self.assertEqual(l['common']['foo'], 'bar')
            self.assertEqual(len(l['logs']), 2)

        self.assertTrue(data_cache.flush_called)

        '''
        given: the values from use case 1
        when: the pipeline is configured as in use case 1
        and when: the first record in the result set does not contain a
                  'LogFile' attribute
        and when: a data cache is specified
        and when: the number of event records to be processed is less than the
                  maximum number of rows
        then: a single Events API post is made containing all labels in the
              'common' property of the logs post and one log for each exported
              and transformed event record, and the cache is flushed
        '''

        cfg = config.Config({})
        newrelic = NewRelicStub()
        query = QueryStub({ 'id': ['Name'] })
        data_cache = DataCacheStub()

        p = pipeline.Pipeline(
            cfg,
            data_cache,
            newrelic,
            DataFormat.LOGS,
            { 'foo': 'bar' },
            {},
            set(),
        )

        self.assertEqual(len(newrelic.logs), 0)

        p.execute(
            session,
            query,
            'https://test.local.test',
            '12345',
            self.event_records,
        )

        self.assertEqual(len(newrelic.logs), 1)
        l = newrelic.logs[0]
        self.assertEqual(len(l), 1)
        l = l[0]
        self.assertTrue('logs' in l)
        self.assertTrue('common' in l)
        self.assertTrue(type(l['common']) is dict)
        self.assertTrue('foo' in l['common'])
        self.assertEqual(l['common']['foo'], 'bar')
        self.assertEqual(len(l['logs']), 3)

        self.assertTrue(data_cache.flush_called)


if __name__ == '__main__':
    unittest.main()
