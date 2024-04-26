import copy
from datetime import datetime, timedelta
import json
import unittest


from . import \
    ApiStub, \
    DataCacheStub, \
    QueryFactoryStub, \
    QueryStub, \
    SessionStub
from newrelic_logging import \
    LoginException, \
    SalesforceApiException
from newrelic_logging import util, config as mod_config
from newrelic_logging.query import receiver


class TestQueryReceiver(unittest.TestCase):
    def setUp(self):
        with open('./tests/sample_log_lines.csv') as stream:
            self.log_rows = stream.readlines()

        with open('./tests/sample_log_lines.json') as stream:
            self.log_lines = json.load(stream)

        with open('./tests/sample_event_records.json') as stream:
            self.event_records = json.load(stream)

        with open('./tests/sample_log_records.json') as stream:
            self.log_records = json.load(stream)

    def test_init_fields_from_log_line_copies_all_fields(self):
        '''
        init_fields_from_log_line() copies all fields in the log line by default
        given: an event type
        and given: a log line
        ane given: a set of event fields mapping
        when: init_fields_from_log_line() is called
        and when: there is no matching mapping for the event type in the event
            fields mapping
        then: copy all fields in log line
        '''

        # setup
        log_line = {
            'foo': 'bar',
            'beep': 'boop',
        }

        # execute
        attrs = receiver.init_fields_from_log_line('ApexCallout', log_line, {})

        # verify
        self.assertTrue(len(attrs) == 2)
        self.assertEqual(attrs['foo'], 'bar')
        self.assertEqual(attrs['beep'], 'boop')

    def test_init_fields_from_log_lines_copies_specified_fields(self):
        '''
        init_fields_from_log_line() copies all fields in the log line by default
        given: an event type
        and given: a log line
        ane given: a set of event fields mapping
        when: init_fields_from_log_line() is called
        and when: there is a matching mapping for the event type in the event
            fields mapping
        then: copy only the fields in the event fields mapping
        '''

        # setup
        log_line = {
            'foo': 'bar',
            'beep': 'boop',
        }

        # execute
        attrs = receiver.init_fields_from_log_line(
            'ApexCallout',
            log_line,
            { 'ApexCallout': ['foo'] }
        )

        # verify
        self.assertTrue(len(attrs) == 1)
        self.assertEqual(attrs['foo'], 'bar')
        self.assertTrue(not 'beep' in attrs)

    def test_pack_log_line_into_log_no_options_or_mapping(self):
        '''
        pack_log_line_into_log() returns a log entry with log line EVENT_TYPE and default timestamp field when no options or mappings are given
        given: a query object
        and given: a record ID
        and given: an event type
        and given: a log line
        and given: a line number,
        and given: an event fields mapping
        when: pack_log_line_into_log() is called
        and when: there is a TIMESTAMP field in the log line
        and when: there is an EVENT_TYPE field in the log line
        and when: there are no query options
        and when: there is no matching event mapping
        then: return a log entry with the message "LogFile $ID row $LINENO"
        and: an attributes dict containing all fields from the log line
        and: an EVENT_TYPE attribute with the log line event type
        and: a timestamp attribute with the log line timestamp
        and: a timestamp field with the timestamp epoch value
        '''

        # setup
        query = QueryStub()

        # execute
        log = receiver.pack_log_line_into_log(
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
        ts = receiver.get_log_line_timestamp({
            'TIMESTAMP': '20240311160000.000'
        })
        self.assertEqual(attrs['timestamp'], int(ts) )
        self.assertTrue('REQUEST_ID' in attrs)
        self.assertTrue('RUN_TIME' in attrs)
        self.assertTrue('CPU_TIME' in attrs)
        self.assertEqual(attrs['REQUEST_ID'], 'YYZ:abcdef123456')
        self.assertEqual(attrs['RUN_TIME'], '2112')
        self.assertEqual(attrs['CPU_TIME'], '10')
        self.assertTrue('timestamp' in log)
        self.assertEqual(attrs['timestamp'], int(ts))

    def test_pack_log_line_into_log_with_event_type_and_rename_timestap_options(self):
        '''
        pack_log_line_into_log() returns a log entry with custom EVENT_TYPE and timestamp fields when event_type and rename_timestamp options are given
        given: a query object
        and given: a record ID
        and given: an event type
        and given: a log line
        and given: a line number,
        and given: an event fields mapping
        when: pack_log_line_into_log() is called
        and when: there is a TIMESTAMP field in the log line
        and when: there is an EVENT_TYPE field in the log line
        and when: the event_type and rename_timestamp query options are given
        and when: there is no matching event mapping
        then: return a log entry with the message "LogFile $ID row $LINENO"
        and: an attributes dict containing all fields from the log line
        and: an EVENT_TYPE attribute with the custom event type
        and: an attribute with the name given in rename_timestamp with the log
            line timestamp
        and: no timestamp field
        '''

        # setup
        query = QueryStub(config={
            'event_type': 'CustomSFEvent',
            'rename_timestamp': 'custom_timestamp',
        })

        # execute
        log = receiver.pack_log_line_into_log(
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
        self.assertEqual(attrs['EVENT_TYPE'], 'CustomSFEvent')
        self.assertEqual(attrs['LogFileId'], '00001111AAAABBBB')
        self.assertTrue('custom_timestamp' in attrs)
        ts = receiver.get_log_line_timestamp({
            'TIMESTAMP': '20240311160000.000'
        })
        self.assertEqual(attrs['custom_timestamp'], int(ts))
        self.assertTrue(not 'timestamp' in log)

    def test_export_log_line_raises_login_exception_if_get_log_file_does(self):
        '''
        export_log_line() raises a LoginException if api.get_log_file() does
        given: an Api instance
        and given: an http session
        and given: a log file path
        and given: a chunk size
        when: export_log_line() is called
        then: api.get_log_file() is called
        and when: api.get_log_file() raises a LoginException
        then: raise a LoginException
        '''

        # setup
        api = ApiStub(raise_login_error=True)
        session = SessionStub()

        # execute/verify
        with self.assertRaises(LoginException) as _:
            lines = receiver.export_log_lines(api, session, '', 100)
            # Have to use next to cause the generator to execute the function
            # else get_log_file() won't get executed and our stub won't have
            # a chance to throw the fake exception.
            next(lines)

    def test_export_log_line_raises_salesforce_exception_if_get_log_file_does(self):
        '''
        export_log_line() raises a SalesforceApiException if api.get_log_file() does
        given: an Api instance
        and given: an http session
        and given: a log file path
        and given: a chunk size
        when: export_log_line() is called
        then: api.get_log_file() is called
        and when: api.get_log_file() raises a SalesforceApiException
        then: raise a SalesforceApiException
        '''

        # setup
        api = ApiStub(raise_error=True)
        session = SessionStub()

        # execute/verify
        with self.assertRaises(SalesforceApiException) as _:
            lines = receiver.export_log_lines(api, session, '', 100)
            # Have to use next to cause the generator to execute the function
            # else get_log_file() won't get executed and our stub won't have
            # a chance to throw the fake exception.
            next(lines)

    def test_export_log_line_returns_generator_with_each_line_on_200(self):
        '''
        export_log_line() returns a generator that yields one line of data for each log line returned
        given: an Api instance
        and given: an http session
        and given: a log file path
        and given: a chunk size
        when: export_log_line() is called
        then: api.get_log_file() is called
        and when: the api.get_log_file() response produces a 200 status code
        then: return a generator iterator that yields one line of data at a time
        '''

        # setup
        api = ApiStub(lines=self.log_rows)
        session = SessionStub()

        # execute
        response = receiver.export_log_lines(api, session, '', 100)

        lines = []
        for line in response:
            lines.append(line)

        # verify
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], self.log_rows[0])
        self.assertEqual(lines[1], self.log_rows[1])
        self.assertEqual(lines[2], self.log_rows[2])

    def test_transform_log_lines_with_no_data_cache(self):
        '''
        transform_log_lines() returns one New Relic Logs API log entry for each log line
        given: an iterable of log rows
        given: a query object
        and given: a record ID
        and given: an object type
        and given: a data cache
        and given: an event fields mapping
        when: transform_log_lines() is called
        and when: the data cache is None
        then: return a generator iterator that yields one New Relic Logs API log
            entry for each row except the header row
        '''

        # setup
        query = QueryStub()

        # execute
        logs = receiver.transform_log_lines(
            self.log_rows,
            query,
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
        self.assertEqual(attrs['timestamp'], 1710172800)

        self.assertTrue('message' in l[1])
        self.assertTrue('attributes', l[1])
        self.assertEqual(l[1]['message'], 'LogFile 00001111AAAABBBB row 1')
        attrs = l[1]['attributes']
        self.assertTrue('EVENT_TYPE' in attrs)
        self.assertTrue('timestamp' in attrs)
        self.assertEqual(attrs['timestamp'], 1710176400)

    def test_transform_log_lines_skips_cached_lines_given_data_cache(self):
        '''
        transform_log_lines() skips cached log lines when a data cache is given
        given: an iterable of log rows
        given: a query object
        and given: a record ID
        and given: an object type
        and given: a data cache
        and given: an event fields mapping
        when: transform_log_lines() is called
        and when: the data cache is not None
        and when: the data cache contains the REQUEST_ID for some of the log
            lines
        then: return a generator iterator that yields one New Relic Logs API log
            entry for each row with a REQUEST_ID not found in the cache
        '''

        # setup
        query = QueryStub()

        # execute
        logs = receiver.transform_log_lines(
            self.log_rows,
            query,
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

    def test_pack_query_record_into_log_given_record_id_and_no_options(self):
        '''
        pack_query_record_into_log() returns a New Relic Logs API log entry with expected attributes given a record id and no query options
        given: a query
        and given: a record id
        and given: a query record
        when: pack_query_record_into_log() is called
        and when: there are no query options
        and when: the record id is not None
        and when: the query record contains a 'type' field in the 'attributes'
            field
        then: return a log with the 'message' attribute set to the object type
            specified in the record's 'attributes.type' field + the created
            date
        and: the 'attributes' attribute contains all attributes
            according to process_query_result, an 'Id' attribute set to the
            passed record ID, an 'EVENT_TYPE' attribute set to the object type
            specified in the record's 'attributes.type' field, and a
            'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        and: the 'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        '''

        # setup
        created_date = self.event_records[0]['CreatedDate']
        timestamp = util.get_timestamp(created_date)

        expected_attrs = {
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

        query = QueryStub()

        # execute
        log = receiver.pack_query_record_into_log(
            query,
            '00001111AAAABBBB',
            self.event_records[0]
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'Account {created_date}')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

    def test_pack_query_record_into_log_given_no_record_id_or_options(self):
        '''
        pack_query_record_into_log() returns a New Relic Logs API log entry with expected attributes given no record id and no query options
        given: a query
        and given: a record id
        and given: a query record
        when: pack_query_record_into_log() is called
        and when: there are no query options
        and when: the record id is None
        and when: the query record contains a 'type' field in the 'attributes'
            field
        then: return a log with the 'message' attribute set to the object type
            specified in the record's 'attributes.type' field + the created
            date
        and: the 'attributes' attribute contains all attributes
            according to process_query_result, an 'Id' attribute set to the
            'Id' value from the record, an 'EVENT_TYPE' attribute set to the
            object type from the record's 'attributes.type' field, and a
            'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        and: the 'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        '''

        # setup
        created_date = self.event_records[0]['CreatedDate']
        timestamp = util.get_timestamp(created_date)

        expected_attrs = {
            'Id': '000012345',
            'Name': 'My Account',
            'BillingCity': None,
            'CreatedDate': created_date,
            'CreatedBy.Name': 'Foo Bar',
            'CreatedBy.Profile.Name': 'Beep Boop',
            'CreatedBy.UserType': 'Bip Bop',
            'EVENT_TYPE': 'Account',
            'timestamp': timestamp,
        }

        query = QueryStub()

        # execute
        log = receiver.pack_query_record_into_log(
            query,
            None,
            self.event_records[0]
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'Account {created_date}')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

    def test_pack_query_record_into_log_given_record_id_and_event_type_option(self):
        '''
        pack_query_record_into_log() returns a New Relic Logs API log entry with expected attributes given a record id and the event_type query option
        given: a query
        and given: a record id
        and given: a query record
        when: pack_query_record_into_log() is called
        and when: the event_type query option is set
        and when: the record id is not None
        and when: the query record contains a 'type' field in the 'attributes'
            field
        then: return a log with the 'message' attribute set to the custom object
            type given in the event_type query option + the created
            date
        and: the 'attributes' attribute contains all attributes
            according to process_query_result, an 'Id' attribute set to the
            'Id' value from the record, an 'EVENT_TYPE' attribute set to the
            custom object type given in the event_type query option, and a
            'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        and: the 'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        '''

        # setup
        created_date = self.event_records[0]['CreatedDate']
        timestamp = util.get_timestamp(created_date)

        expected_attrs = {
            'Id': '00001111AAAABBBB',
            'Name': 'My Account',
            'BillingCity': None,
            'CreatedDate': created_date,
            'CreatedBy.Name': 'Foo Bar',
            'CreatedBy.Profile.Name': 'Beep Boop',
            'CreatedBy.UserType': 'Bip Bop',
            'EVENT_TYPE': 'CustomEvent',
            'timestamp': timestamp,
        }

        query = QueryStub(config={ 'event_type': 'CustomEvent' })

        # execute
        log = receiver.pack_query_record_into_log(
            query,
            '00001111AAAABBBB',
            self.event_records[0]
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'CustomEvent {created_date}')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

    def test_pack_query_record_into_log_given_record_id_and_no_attributes_field(self):
        '''
        pack_query_record_into_log() returns a New Relic Logs API log entry with expected attributes given a record id and a record with no 'attributes' field
        given: a query
        and given: a record id
        and given: a query record
        when: pack_query_record_into_log() is called
        and when: there are no query options
        and when: the record id is not None
        and when: the query record does not contain an 'attributes' field
        then: return a log with the 'message' attribute set to the default
            object type + the created date
        and: the 'attributes' attribute contains all attributes
            according to process_query_result, an 'Id' attribute set to the
            'Id' value from the record, no 'EVENT_TYPE' attribute, and a
            'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        and: the 'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        '''

        # setup
        created_date = self.event_records[0]['CreatedDate']
        timestamp = util.get_timestamp(created_date)

        expected_attrs = {
            'Id': '00001111AAAABBBB',
            'Name': 'My Account',
            'BillingCity': None,
            'CreatedDate': created_date,
            'CreatedBy.Name': 'Foo Bar',
            'CreatedBy.Profile.Name': 'Beep Boop',
            'CreatedBy.UserType': 'Bip Bop',
            'timestamp': timestamp,
        }

        query = QueryStub()
        event_record = copy.deepcopy(self.event_records[0])
        event_record.pop('attributes')

        # execute
        log = receiver.pack_query_record_into_log(
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

    def test_pack_query_record_into_log_given_record_id_and_attributes_field_not_dict(self):
        '''
        pack_query_record_into_log() returns a New Relic Logs API log entry with expected attributes given a record id and a record with an attributes field that is not a dictionary
        given: a query
        and given: a record id
        and given: a query record
        when: pack_query_record_into_log() is called
        and when: there are no query options
        and when: the record id is not None
        and when: the query record does contain an 'attributes' field but it is
            not a dictionary
        then: return a log with the 'message' attribute set to the default
            object type + the created date
        and: the 'attributes' attribute contains all attributes
            according to process_query_result, an 'Id' attribute set to the
            'Id' value from the record, no 'EVENT_TYPE' attribute, and a
            'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        and: the 'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        '''

        # setup
        created_date = self.event_records[0]['CreatedDate']
        timestamp = util.get_timestamp(created_date)

        expected_attrs = {
            'Id': '00001111AAAABBBB',
            'Name': 'My Account',
            'BillingCity': None,
            'CreatedDate': created_date,
            'CreatedBy.Name': 'Foo Bar',
            'CreatedBy.Profile.Name': 'Beep Boop',
            'CreatedBy.UserType': 'Bip Bop',
            'timestamp': timestamp,
        }

        query = QueryStub()
        event_record = copy.deepcopy(self.event_records[0])
        event_record['attributes'] = 'test'

        # execute
        log = receiver.pack_query_record_into_log(
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

    def test_pack_query_record_into_log_given_record_id_and_no_attributes_type_field(self):
        '''
        pack_query_record_into_log() returns a New Relic Logs API log entry with expected attributes given a record id and a record with an attributes field but not type field
        given: a query
        and given: a record id
        and given: a query record
        when: pack_query_record_into_log() is called
        and when: there are no query options
        and when: the record id is not None
        and when: the query record does not contain a 'type' field in the
            'attributes' field
        then: return a log with the 'message' attribute set to the default
            object type + the created date
        and: the 'attributes' attribute contains all attributes
            according to process_query_result, an 'Id' attribute set to the
            'Id' value from the record, no 'EVENT_TYPE' attribute, and a
            'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        and: the 'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        '''

        # setup
        created_date = self.event_records[0]['CreatedDate']
        timestamp = util.get_timestamp(created_date)

        expected_attrs = {
            'Id': '00001111AAAABBBB',
            'Name': 'My Account',
            'BillingCity': None,
            'CreatedDate': created_date,
            'CreatedBy.Name': 'Foo Bar',
            'CreatedBy.Profile.Name': 'Beep Boop',
            'CreatedBy.UserType': 'Bip Bop',
            'timestamp': timestamp,
        }

        query = QueryStub()
        event_record = copy.deepcopy(self.event_records[0])
        event_record['attributes'].pop('type')

        # execute
        log = receiver.pack_query_record_into_log(
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

    def test_pack_query_record_into_log_given_record_id_and_attributes_type_field_not_str(self):
        '''
        pack_query_record_into_log() returns a New Relic Logs API log entry with expected attributes given a record id and a record with an attributes type field that is not a string
        given: a query
        and given: a record id
        and given: a query record
        when: pack_query_record_into_log() is called
        and when: there are no query options
        and when: the record id is not None
        and when: the query record does contains a 'type' field in the
            'attributes' field but it is not a string
        then: return a log with the 'message' attribute set to the default
            object type + the created date
        and: the 'attributes' attribute contains all attributes
            according to process_query_result, an 'Id' attribute set to the
            'Id' value from the record, no 'EVENT_TYPE' attribute, and a
            'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        and: the 'timestamp' attribute set to the epoch value representing the
            record's 'CreatedDate' field
        '''

        # setup
        created_date = self.event_records[0]['CreatedDate']
        timestamp = util.get_timestamp(created_date)

        expected_attrs = {
            'Id': '00001111AAAABBBB',
            'Name': 'My Account',
            'BillingCity': None,
            'CreatedDate': created_date,
            'CreatedBy.Name': 'Foo Bar',
            'CreatedBy.Profile.Name': 'Beep Boop',
            'CreatedBy.UserType': 'Bip Bop',
            'timestamp': timestamp,
        }

        query = QueryStub()
        event_record = copy.deepcopy(self.event_records[0])
        event_record['attributes']['type'] = 12345

        # execute
        log = receiver.pack_query_record_into_log(
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

    def test_pack_query_record_into_log_given_record_id_and_timestamp_attr_option(self):
        '''
        pack_query_record_into_log() returns a New Relic Logs API log entry with expected attributes given a record id and the timestamp_attr query option
        given: a query
        and given: a record id
        and given: a query record
        when: pack_query_record_into_log() is called
        and when: the timestamp_attr query option is set
        and when: the record id is not None
        and when: the query record contains a 'type' field in the 'attributes'
            field
        then: return a log with the 'message' attribute set to the object type
            specified in the record's 'attributes.type' field + the created
            date
        and: the 'attributes' attribute contains all attributes
            according to process_query_result, an 'Id' attribute set to the
            passed record ID, an 'EVENT_TYPE' attribute set to the object type
            specified in the record's 'attributes.type' field, and a
            'timestamp' attribute set to the timestamp from the field specified
            in the 'timestamp_attr' query option
        and: the 'timestamp' attribute set to the timestamp from the field
            specified in the 'timestamp_attr' query option
        '''

        # setup
        created_date = self.event_records[0]['CreatedDate']
        created_date_2 = self.event_records[1]['CreatedDate']
        timestamp = util.get_timestamp(created_date_2)

        expected_attrs = {
            'Id': '00001111AAAABBBB',
            'Name': 'My Account',
            'BillingCity': None,
            'CreatedDate': created_date,
            'CustomDate': created_date_2,
            'CreatedBy.Name': 'Foo Bar',
            'CreatedBy.Profile.Name': 'Beep Boop',
            'CreatedBy.UserType': 'Bip Bop',
            'EVENT_TYPE': 'Account',
            'timestamp': timestamp,
        }

        query = QueryStub(config={ 'timestamp_attr': 'CustomDate' })
        event_record = copy.deepcopy(self.event_records[0])
        event_record['CustomDate'] = created_date_2

        # execute
        log = receiver.pack_query_record_into_log(
            query,
            '00001111AAAABBBB',
            event_record,
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'Account {created_date_2}')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

    def test_pack_query_record_into_log_given_record_id_and_timestamp_attr_option_with_missing_attr(self):
        '''
        pack_query_record_into_log() returns a New Relic Logs API log entry with expected attributes given a record id and the timestamp_attr query option but the attribute is missing
        given: a query
        and given: a record id
        and given: a query record
        when: pack_query_record_into_log() is called
        and when: the timestamp_attr query option is set
        and when: the attribute specified by the timestamp_attr option is not in
            the query record
        and when: the record id is not None
        and when: the query record contains a 'type' field in the 'attributes'
            field
        then: return a log with the 'message' attribute set to the object type
            specified in the record's 'attributes.type' field but does not
            include a date
        and: the 'attributes' attribute contains all attributes
            according to process_query_result, an 'Id' attribute set to the
            passed record ID, an 'EVENT_TYPE' attribute set to the object type
            specified in the record's 'attributes.type' field, and a
            'timestamp' attribute set to the current time
        and: the 'timestamp' attribute set to the current time
        '''

        # setup
        __now = datetime.now()

        def _now():
            nonlocal __now
            return __now

        util._NOW = _now

        created_date = self.event_records[0]['CreatedDate']
        timestamp = util.get_timestamp()

        expected_attrs = {
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

        query = QueryStub(config={ 'timestamp_attr': 'NotPresent' })

        # execute
        log = receiver.pack_query_record_into_log(
            query,
            '00001111AAAABBBB',
            self.event_records[0],
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'Account')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

    def test_pack_query_record_into_log_given_record_id_with_no_created_date(self):
        '''
        pack_query_record_into_log() returns a New Relic Logs API log entry with expected attributes given a record id and no a record with no CreatedDate
        given: a query
        and given: a record id
        and given: a query record
        when: pack_query_record_into_log() is called
        and when: there are no query options
        and when: the record id is not None
        and when: the query record contains a 'type' field in the 'attributes'
            field
        and when: the query record does not contain a `CreatedDate` field
        then: return a log with the 'message' attribute set to the object type
            specified in the record's 'attributes.type' field but does not
            include a date
        and: the 'attributes' attribute contains all attributes
            according to process_query_result, an 'Id' attribute set to the
            passed record ID, an 'EVENT_TYPE' attribute set to the object type
            specified in the record's 'attributes.type' field, and a
            'timestamp' attribute set to the current time
        and: the 'timestamp' attribute set to the current time
        '''

        # setup
        __now = datetime.now()

        def _now():
            nonlocal __now
            return __now

        util._NOW = _now

        timestamp = util.get_timestamp()

        expected_attrs = {
            'Id': '00001111AAAABBBB',
            'Name': 'My Account',
            'BillingCity': None,
            'CreatedBy.Name': 'Foo Bar',
            'CreatedBy.Profile.Name': 'Beep Boop',
            'CreatedBy.UserType': 'Bip Bop',
            'EVENT_TYPE': 'Account',
            'timestamp': timestamp,
        }

        query = QueryStub()
        event_record = copy.deepcopy(self.event_records[0])
        event_record.pop('CreatedDate')

        # execute
        log = receiver.pack_query_record_into_log(
            query,
            '00001111AAAABBBB',
            event_record,
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue('timestamp' in log)
        self.assertEqual(log['message'], f'Account')
        self.assertEqual(log['attributes'], expected_attrs)
        self.assertEqual(log['timestamp'], timestamp)

    def test_pack_query_record_into_log_given_record_id_and_rename_timestamp_option(self):
        '''
        pack_query_record_into_log() returns a New Relic Logs API log entry with expected attributes given a record id and the rename_timestamp query option
        given: a query
        and given: a record id
        and given: a query record
        when: pack_query_record_into_log() is called
        and when: the rename_timestamp query option is set
        and when: the record id is not None
        and when: the query record contains a 'type' field in the 'attributes'
            field
        then: return a log with the 'message' attribute set to the object type
            specified in the record's 'attributes.type' field + the created
            date
        and: the 'attributes' attribute contains all attributes
            according to process_query_result, an 'Id' attribute set to the
            passed record ID, an 'EVENT_TYPE' attribute set to the object type
            specified in the record's 'attributes.type' field, an attribute with
            the name specified in the 'rename_timestamp' query option set to the
            'CreatedDate' field, and no 'timestamp' attribute.
        and: no 'timestamp' attribute
        '''

        # setup
        created_date = self.event_records[0]['CreatedDate']
        timestamp = util.get_timestamp(created_date)

        expected_attrs = {
            'Id': '00001111AAAABBBB',
            'Name': 'My Account',
            'BillingCity': None,
            'CreatedDate': created_date,
            'CreatedBy.Name': 'Foo Bar',
            'CreatedBy.Profile.Name': 'Beep Boop',
            'CreatedBy.UserType': 'Bip Bop',
            'EVENT_TYPE': 'Account',
            'custom_timestamp': timestamp,
        }

        query = QueryStub(config={ 'rename_timestamp': 'custom_timestamp' })

        # execute
        log = receiver.pack_query_record_into_log(
            query,
            '00001111AAAABBBB',
            self.event_records[0]
        )

        # verify
        self.assertTrue('message' in log)
        self.assertTrue('attributes' in log)
        self.assertTrue(not 'timestamp' in log)
        self.assertEqual(log['message'], f'Account {created_date}')
        self.assertEqual(log['attributes'], expected_attrs)

    def test_transform_query_records_given_record_has_id(self):
        '''
        transform_query_records() returns New Relic Logs API log entries with Id attributes for query records with Id fields
        given: a list of query records
        and given: a query
        and given: a data cache
        when: transform_query_records() is called
        and when: the record contains an 'Id' field
        and when: the data cache is None
        then: return a log with the 'Id' attribute in the log 'attributes'
            attribute set to the value of the 'Id' field
        '''

        # setup
        query = QueryStub()

        # execute
        logs = receiver.transform_query_records(
            self.event_records[0:2],
            query,
            None,
        )

        l = []

        for log in logs:
            l.append(log)

        # verify
        self.assertEqual(len(l), 2)
        self.assertTrue('Id' in l[0]['attributes'])
        self.assertTrue('Id' in l[1]['attributes'])
        self.assertEqual(l[0]['attributes']['Id'], '000012345')
        self.assertEqual(l[1]['attributes']['Id'], '000054321')

    def test_transform_query_records_given_record_missing_id(self):
        '''
        transform_query_records() returns New Relic Logs API log entries with no Id attributes for query records with no Id field
        given: a list of query records
        and given: a query
        and given: a data cache
        when: transform_query_records() is called
        and when: the record does not contain an 'Id' field and the 'id' query
            option is not set
        and when: the data cache is None
        then: return a log with no 'Id' attribute in the log 'attributes'
            attribute
        '''
        # setup
        query = QueryStub()

        # execute
        logs = receiver.transform_query_records(
            self.event_records[2:],
            query,
            None,
        )

        l = []

        for log in logs:
            l.append(log)

        # verify
        self.assertEqual(len(l), 1)
        self.assertTrue(not 'Id' in l[0]['attributes'])

    def test_transform_query_records_given_id_option(self):
        '''
        transform_query_records() returns New Relic Logs API log entries with generated Id attributes for query records with no Id field and given the id query option
        given: a list of query records
        and given: a query
        and given: a data cache
        when: transform_query_records() is called
        and when: the record does not contain an 'Id' field
        and when: the 'id' query option is set
        and when: the record contains the field set in the 'id' query option
        and when: the data cache is None
        then: return a log with a generated 'Id' attribute in the log
            'attributes' attribute
        '''
        # setup
        query = QueryStub(config={ 'id': ['Name'] })
        customId = util.generate_record_id([ 'Name' ], self.event_records[2])

        # execute
        logs = receiver.transform_query_records(
            self.event_records[2:],
            query,
            None,
        )

        l = []

        for log in logs:
            l.append(log)

        # verify
        self.assertEqual(len(l), 1)
        self.assertTrue('Id' in l[0]['attributes'])
        self.assertEqual(l[0]['attributes']['Id'], customId)

    def test_transform_query_records_given_data_cache(self):
        '''
        transform_query_records() skips cached records when a data cache os given
        given: a list of query records
        and given: a query
        and given: a data cache
        when: transform_query_records() is called
        and when: the record contains an 'Id' field
        and when: the data cache is None
        then: return a log with the 'Id' attribute in the log 'attributes'
            attribute set to the value of the 'Id' field
        '''

        # setup
        query = QueryStub()
        data_cache = DataCacheStub(
            cached_logs={},
            cached_records=[ '000012345', '000054321' ]
        )

        # execute
        logs = receiver.transform_query_records(
            self.event_records,
            query,
            data_cache,
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

    def test_is_logs_enabled_given_instance_config_has_no_logs_enabled(self):
        '''
        is_logs_enabled() returns the default (True) when the 'logs_enabled' property is not in the instance config
        given: an instance config
        when: is_logs_enabled() is called
        and when: the instance config does not contain a 'logs_enabled' property
        then: return True
        '''

        # setup
        instance_config = mod_config.Config({})

        # execute
        val = receiver.is_logs_enabled(instance_config)

        # verify
        self.assertTrue(val)

    def test_is_logs_enabled_given_logs_enabled_in_config(self):
        '''
        is_logs_enabled() returns the boolean value of the 'logs_enabled' property when present in the instance config
        given: an instance config
        when: is_logs_enabled() is called
        and when: the instance config contains a 'logs_enabled' property
        then: return the boolean value of the 'logs_enabled' property
        '''

        # setup
        instance_config = mod_config.Config({ 'logs_enabled': 'off' })

        # execute
        val = receiver.is_logs_enabled(instance_config)

        # verify
        self.assertFalse(val)

    def test_get_instance_queries_returns_none_when_instance_config_has_no_queries(self):
        '''
        get_instance_queries() returns None when no queries are present in the instance config
        given: an instance config
        when: get_instance_queries() is called
        and when: the instance config does not contain a 'queries' property
        then: return None
        '''

        # setup
        instance_config = mod_config.Config({})

        # execute
        val = receiver.get_instance_queries(instance_config)

        # verify
        self.assertIsNone(val)

    def test_get_instance_queries_returns_none_when_instance_config_queries_not_list(self):
        '''
        get_instance_queries() returns None when a queries property is in the instance config but it is not a list
        given: an instance config
        when: get_instance_queries() is called
        and when: the instance config contains a queries property
        and when: the property is not a list
        then: return None
        '''

        # setup
        instance_config = mod_config.Config({ 'queries': 12345 })

        # execute
        val = receiver.get_instance_queries(instance_config)

        # verify
        self.assertIsNone(val)

    def test_get_instance_queries_returns_queries_when_instance_config_has_queries(self):
        '''
        get_instance_queries() returns the queries list when a queries property is in the instance config and is a list
        given: an instance config
        when: get_instance_queries() is called
        and when: the instance config contains a queries property
        and when: the property is a list
        then: return the queries list
        '''

        # setup
        instance_config = mod_config.Config({
            'queries': ['SELECT * FROM SetupAuditTrail'],
        })

        # execute
        val = receiver.get_instance_queries(instance_config)

        # verify
        self.assertIsNotNone(val)
        self.assertEqual(len(val), 1)
        self.assertEqual(val[0], 'SELECT * FROM SetupAuditTrail')

    def test_get_default_query_returns_logdate_query_given_logdate_date_field(self):
        '''
        get_default_query() returns the LogDate query when the lower cased date field parameter is 'logdate'
        given: an instance config
        when: get_default_query() is called
        and when: the lower cased date field is 'logdate'
        then: return the LogDate query
        '''

        # execute
        query = receiver.get_default_query('LogDate')

        # verify
        self.assertEqual(query, receiver.SALESFORCE_LOG_DATE_QUERY)

    def test_get_default_query_returns_createddate_query_given_not_logdate_date_field(self):
        '''
        get_default_query() returns the CreatedDate query when the lower cased date field parameter is not 'logdate'
        given: an instance config
        when: get_default_query() is called
        and when: the lower cased date field is not 'logdate'
        then: return the CreatedDate query
        '''

        # execute
        query = receiver.get_default_query('CreateDate')

        # verify
        self.assertEqual(query, receiver.SALESFORCE_CREATED_DATE_QUERY)

    def test_build_queries_returns_empty_list_when_no_queries_and_logs_disabled(self):
        '''
        build_queries() returns the empty list given no instance or global queries and logs disabled
        given: an instance config
        when: build_queries() is called
        and when: there are no instance queries
        and when: there are no global queries
        and when: logs are disabled
        then: return the empty list
        '''

        # setup
        instance_config = mod_config.Config({ 'logs_enabled': 'off' })

        # execute
        val = receiver.build_queries(instance_config, None, 'LogDate')

        # verify
        self.assertIsNotNone(val)
        self.assertEqual([], val)

    def test_build_queries_returns_default_query_when_no_queries_and_logs_enabled(self):
        '''
        build_queries() returns a list with the default query given no instance or global queries and logs enabled
        given: an instance config
        when: build_queries() is called
        and when: there are no instance queries
        and when: there are no global queries
        and when: logs are enabled
        then: return a list with the default query
        '''

        # setup
        instance_config = mod_config.Config({})

        # execute
        val = receiver.build_queries(instance_config, None, 'LogDate')

        # verify
        self.assertIsNotNone(val)
        self.assertEqual(len(val), 1)
        self.assertEqual([{ 'query': receiver.SALESFORCE_LOG_DATE_QUERY }], val)

    def test_build_queries_returns_instance_queries_when_instance_config_has_queries(self):
        '''
        build_queries() returns a list with the instance queries when the queries property is in the instance config
        given: an instance config
        when: build_queries() is called
        and when: there are instance queries in the instance config
        and when: there are no global queries
        then: return the instance queries
        '''

        # setup
        instance_config = mod_config.Config({
            'queries': [{ 'query': 'SELECT * FROM SetupAuditTrail' }],
        })

        # execute
        val = receiver.build_queries(instance_config, None, 'LogDate')

        # verify
        self.assertIsNotNone(val)
        self.assertEqual([{ 'query': 'SELECT * FROM SetupAuditTrail' }], val)

    def test_build_queries_returns_global_queries_when_given(self):
        '''
        build_queries() returns a list with the global queries given global queries are passed in
        when: build_queries() is called
        and when: there are no instance queries
        and when: global queries are passed in
        then: return the global queries
        '''

        # setup
        instance_config = mod_config.Config({})

        # execute
        val = receiver.build_queries(
            instance_config,
            [{ 'query': 'SELECT * FROM SetupAuditTrail' }],
            'LogDate',
        )

        # verify
        self.assertIsNotNone(val)
        self.assertEqual([{ 'query': 'SELECT * FROM SetupAuditTrail' }], val)

    def test_build_queries_returns_instance_queries_and_global_queries_when_both_present(self):
        '''
        build_queries() returns a list with both the queries from the instance config and the global queries when both are specified
        when: build_queries() is called
        and when: there are instance queries in the instance config
        and when: global queries are passed in
        then: return a list containing the instance queries and global queries
        '''

        # setup
        instance_config = mod_config.Config({
            'queries': [{ 'query': 'SELECT * FROM SetupAuditTrail' }],
        })
        # execute
        val = receiver.build_queries(
            instance_config,
            [{ 'query': 'SELECT * FROM EventLogFile' }],
            'LogDate',
        )

        # verify
        self.assertIsNotNone(val)
        self.assertEqual([
            { 'query': 'SELECT * FROM SetupAuditTrail' },
            { 'query': 'SELECT * FROM EventLogFile' },
        ], val)

    def test_query_receiver_execute_yields_nothing_given_no_queries(self):
        '''
        QueryReceiver.execute() does not execute any queries when given no queries and yields no results
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: an http session
        when: QueryReceiver.execute() is called
        and when: no queries are specified
        and when: the data cache is None
        then: yield no results
        '''

        # setup
        api = ApiStub()
        query_factory = QueryFactoryStub()
        session = SessionStub()

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            [],
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        # execute
        iter = r.execute(session)

        logs = []
        for log in iter:
            logs.append(log)

        # verify

        self.assertEqual(len(logs), 0)

    def test_query_receiver_execute_yields_all_results_given_multiple_queries(self):
        '''
        QueryReceiver.execute() executes each query given multiple queries and yields results from each query
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: an http session
        when: QueryReceiver.execute() is called
        and when: one or more queries are specified
        and when: the data cache is None
        then: execute each query
        and: yield the combined results of all queries
        '''

        # setup
        api = ApiStub()
        query_factory = QueryFactoryStub()
        queries = [
            {
                'query': 'foo',
                'results': [{ 'foo': 'bar' }]
            },
            {
                'query': 'bar',
                'results': [{ 'bar': 'foo' }]
            },
            {
                'query': 'beep',
                'results': [{ 'beep': 'boop' }]
            },
            {
                'query': 'boop',
                'results': [{ 'boop': 'beep' }]
            },
        ]
        session = SessionStub()

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        # execute
        iter = r.execute(session)

        logs = []
        for log in iter:
            logs.append(log)

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

        self.assertEqual(len(logs), 4)
        log = logs[0]
        self.assertEqual(logs[0]['attributes']['foo'], 'bar')

    def test_query_receiver_execute_yields_nothing_given_query_returns_no_result(self):
        '''
        QueryReceiver.execute() yields no results when the query result is not truthy
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: an http session
        when: QueryReceiver.execute() is called
        and when: a query is specified
        and when: the data cache is None
        then: execute the query
        and when: the query result is not truthy
        then: yield no results
        '''

        # setup
        api = ApiStub()
        query = QueryStub(result=None)
        query_factory = QueryFactoryStub(query)
        queries = [
            {
                'query': 'foo',
            },
        ]
        session = SessionStub()

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        # execute
        iter = r.execute(session)

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 0)

    def test_query_receiver_execute_yields_nothing_given_query_returns_no_records(self):
        '''
        QueryReceiver.execute() yields no results when the query result has no 'records' key
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: an http session
        when: QueryReceiver.execute() is called
        and when: a query is specified
        and when: the data cache is None
        then: execute the query
        and when: the query result has no 'records' key
        then: yield no results
        '''

        # setup
        api = ApiStub()
        query = QueryStub(result={ 'foo': 'bar' })
        query_factory = QueryFactoryStub(query)
        queries = [
            {
                'query': 'foo',
            },
        ]
        session = SessionStub()

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        # execute
        iter = r.execute(session)

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 0)

    def test_query_receiver_execute_raises_login_exception_if_query_execute_does(self):
        '''
        QueryReceiver.execute() raises a LoginException if query.execute() does
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: an http session
        when: QueryReceiver.execute() is called
        and when: a query is specified
        and when: the data cache is None
        and when: query.execute() raises a LoginException
        then: QueryReceiver.execute() raises a LoginException
        '''

        # setup
        api = ApiStub()
        query = QueryStub(raise_login_error=True)
        query_factory = QueryFactoryStub(query)
        queries = [
            {
                'query': 'foo',
            },
        ]
        session = SessionStub()

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        # execute / verify
        with self.assertRaises(LoginException) as _:
            iter = r.execute(session)
            # Have to use next to cause the generator to execute the function
            # else get_log_file() won't get executed and our stub won't have
            # a chance to throw the fake exception.
            next(iter)

    def test_query_receiver_execute_raises_salesforce_exception_if_query_execute_does(self):
        '''
        QueryReceiver.execute() raises a SalesforceApiException if query.execute() does
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: an http session
        when: QueryReceiver.execute() is called
        and when: a query is specified
        and when: the data cache is None
        and when: query.execute() raises a SalesforceApiException
        then: QueryReceiver.execute() raises a SalesforceApiException
        '''

        # setup
        api = ApiStub()
        query = QueryStub(raise_error=True)
        query_factory = QueryFactoryStub(query)
        queries = [
            {
                'query': 'foo',
            },
        ]
        session = SessionStub()

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        # execute / verify
        with self.assertRaises(SalesforceApiException) as _:
            iter = r.execute(session)
            # Have to use next to cause the generator to execute the function
            # else get_log_file() won't get executed and our stub won't have
            # a chance to throw the fake exception.
            next(iter)

    def test_query_receiver_process_log_record_yields_log_entries_given_log_lines(self):
        '''
        QueryReceiver.process_log_record() yields one log entry for each log line
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: an http session
        and given: a query object
        and given: a log record
        when: QueryReceiver.process_log_record() is called
        and when: a log record is processed
        and when: the data cache is None
        then: yield one log entry for each log line
        '''

        # setup
        api = ApiStub(lines=self.log_rows)
        session = SessionStub()
        query = QueryStub()
        query_factory = QueryFactoryStub()
        queries = [
            {
                'query': 'foo',
            },
        ]
        record = self.log_records[0]

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        iter = r.process_log_record(
            session,
            query,
            record,
        )

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 2)

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

    def test_query_receiver_process_log_record_skips_cached_records(self):
        '''
        QueryReceiver.process_log_record() does not yield log entries for cached log records
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: an http session
        and given: a query object
        and given: a log record
        when: QueryReceiver.process_log_record() is called
        and when: a data cache is specified
        and when: a record ID matches a record ID in the data cache
        then: do not yield a log entry for the cached record
        '''

        # setup
        api = ApiStub(lines=self.log_rows)
        data_cache = DataCacheStub(skip_record_ids=['00001111AAAABBBB'])
        session = SessionStub()
        query = QueryStub()
        query_factory = QueryFactoryStub()
        queries = [
            {
                'query': 'foo',
            },
        ]
        record = self.log_records[0]

        # execute
        r = receiver.QueryReceiver(
            data_cache,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        iter = r.process_log_record(
            session,
            query,
            record,
        )

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 0)

    def test_query_receiver_process_log_record_yields_cached_records_when_interval_not_hourly(self):
        '''
        QueryReceiver.process_log_record() yields log entries even for cached log records when the generation interval is not Hourly
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: an http session
        and given: a query object
        and given: a log record
        when: QueryReceiver.process_log_record() is called
        and when: a data cache is specified
        and when: a record ID matches a record ID in the data cache
        and when: the generation interval is not 'Hourly'
        then: yield one log entry for each log line even for cached records
        '''

        # setup
        api = ApiStub(lines=self.log_rows)
        data_cache = DataCacheStub(skip_record_ids=['00001111AAAABBBB'])
        session = SessionStub()
        query = QueryStub()
        query_factory = QueryFactoryStub()
        queries = [
            {
                'query': 'foo',
            },
        ]
        record = copy.deepcopy(self.log_records[0])
        record['Interval'] = 'Daily'

        # execute
        r = receiver.QueryReceiver(
            data_cache,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Daily',
            4096,
        )

        iter = r.process_log_record(
            session,
            query,
            record,
        )

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 2)

    def test_query_receiver_process_log_record_raises_login_exception_if_export_log_lines_does(self):
        '''
        QueryReceiver.process_log_record() raises a LoginException if export_log_lines() does
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: an http session
        and given: a query object
        and given: a log record
        when: QueryReceiver.process_log_record() is called
        and when: no data cache is specified
        and when: export_log_lines() raises a LoginException
        then: raise a LoginException
        '''

        # setup
        api = ApiStub(raise_login_error=True)
        session = SessionStub()
        query = QueryStub()
        query_factory = QueryFactoryStub()
        queries = [
            {
                'query': 'foo',
            },
        ]
        record = self.log_records[0]

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Daily',
            4096,
        )

        with self.assertRaises(LoginException) as _:
            iter = r.process_log_record(
                session,
                query,
                record,
            )
            # Have to use next to cause the generator to execute the function
            # else get_log_file() won't get executed and our stub won't have
            # a chance to throw the fake exception.
            next(iter)

    def test_query_receiver_process_log_record_raises_salesforce_exception_if_export_log_lines_does(self):
        '''
        QueryReceiver.process_log_record() raises a SalesforceApiException if export_log_lines() does
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: an http session
        and given: a query object
        and given: a log record
        when: QueryReceiver.process_log_record() is called
        and when: no data cache is specified
        and when: export_log_lines() raises a SalesforceApiException
        then: raise a SalesforceApiException
        '''

        # setup
        api = ApiStub(raise_error=True)
        session = SessionStub()
        query = QueryStub()
        query_factory = QueryFactoryStub()
        queries = [
            {
                'query': 'foo',
            },
        ]
        record = self.log_records[0]

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Daily',
            4096,
        )

        with self.assertRaises(SalesforceApiException) as _:
            iter = r.process_log_record(
                session,
                query,
                record,
            )
            # Have to use next to cause the generator to execute the function
            # else get_log_file() won't get executed and our stub won't have
            # a chance to throw the fake exception.
            next(iter)

    def test_query_receiver_process_query_records_yields_log_entries_given_query_records(self):
        '''
        QueryReceiver.process_query_records() yields one log entry for each query record
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: a query object
        and given: a set of query records
        when: QueryReceiver.process_query_records() is called
        and when: no data cache is specified
        and when: the data cache is None
        then: yield one log entry for each query record
        '''

        # setup
        api = ApiStub(lines=self.log_rows)
        session = SessionStub()
        query = QueryStub(config={ 'id': ['Name'] })
        query_factory = QueryFactoryStub()
        queries = [
            {
                'query': 'foo',
            },
        ]

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Daily',
            4096,
        )

        iter = r.process_query_records(
            query,
            self.event_records,
        )

        logs = []
        for log in iter:
            logs.append(log)

        # verify
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

    def test_query_receiver_process_records_yields_log_entries_given_log_records(self):
        '''
        QueryReceiver.process_records() yields one log entry for each log line given log records
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: a query object
        and given: a set of query records
        when: QueryReceiver.process_records() is called
        and when: no data cache is specified
        and when: the first query record is a 'LogFile' record
        and when: the data cache is None
        then: yield one log entry for each log line
        '''

        # setup
        api = ApiStub(lines=self.log_rows)
        session = SessionStub()
        query = QueryStub()
        query_factory = QueryFactoryStub()
        queries = [
            {
                'query': 'foo',
            },
        ]
        records = self.log_records

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        iter = r.process_records(
            session,
            query,
            records,
        )

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 4)

    def test_query_receiver_process_records_yields_log_entries_given_log_records_and_flushes_cache_given_cache(self):
        '''
        QueryReceiver.process_records() yields one log entry for each log line given log records and flushes the cache given a data cache
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: a query object
        and given: a set of query records
        when: QueryReceiver.process_records() is called
        and when: no data cache is specified
        and when: the first query record is a 'LogFile' record
        and when: a data cache is specified
        then: yield one log entry for each log line
        and: flush the data cache
        '''

        # setup
        api = ApiStub(lines=self.log_rows)
        data_cache = DataCacheStub()
        session = SessionStub()
        query = QueryStub()
        query_factory = QueryFactoryStub()
        queries = [
            {
                'query': 'foo',
            },
        ]
        records = self.log_records

        # execute
        r = receiver.QueryReceiver(
            data_cache,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        iter = r.process_records(
            session,
            query,
            records,
        )

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 4)
        self.assertTrue(data_cache.flush_called)

    def test_query_receiver_process_records_yields_log_entries_given_query_records(self):
        '''
        QueryReceiver.process_records() yields one log entry for each query record given query records
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: a query object
        and given: a set of query records
        when: QueryReceiver.process_records() is called
        and when: no data cache is specified
        and when: the first query record is not a 'LogFile' record
        and when: the data cache is None
        then: yield one log entry for each query record
        '''

        # setup
        api = ApiStub()
        session = SessionStub()
        query = QueryStub()
        query_factory = QueryFactoryStub()
        queries = [
            {
                'query': 'foo',
            },
        ]
        records = self.event_records

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        iter = r.process_records(
            session,
            query,
            records,
        )

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 3)

    def test_query_receiver_process_records_yields_log_entries_given_query_records_and_flushes_cache_given_cache(self):
        '''
        QueryReceiver.process_records() yields one log entry for each query record given query records and flushes the cache given a data cache
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        and given: a query object
        and given: a set of query records
        when: QueryReceiver.process_records() is called
        and when: a data cache is specified
        and when: the first query record is not a 'LogFile' record
        and when: the data cache is None
        then: yield one log entry for each query record
        '''

        # setup
        api = ApiStub()
        data_cache = DataCacheStub()
        session = SessionStub()
        query = QueryStub()
        query_factory = QueryFactoryStub()
        queries = [
            {
                'query': 'foo',
            },
        ]
        records = self.event_records

        # execute
        r = receiver.QueryReceiver(
            data_cache,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        iter = r.process_records(
            session,
            query,
            records,
        )

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 3)
        self.assertTrue(data_cache.flush_called)

    def test_query_receiver_slide_time_range(self):
        '''
        QueryReceiver.slide_time_range() updates the last_to_timestamp
        given: a data cache
        and given: an api
        and given: a query factory
        and given: a list of queries
        and given: an event type fields mapping
        and given: an initial delay value
        and given: a time lag minutes value
        and given: a generation interval
        and given: a read chunk size
        when: QueryReceiver.process_records() is called
        and when: a data cache is specified
        and when: the first query record is not a 'LogFile' record
        and when: the data cache is None
        then: yield one log entry for each query record
        '''

        # setup
        _now = datetime.utcnow()

        def _utcnow():
            nonlocal _now
            return _now

        util._UTCNOW = _utcnow

        api = ApiStub()
        query_factory = QueryFactoryStub()
        queries = [
            {
                'query': 'foo',
            },
        ]

        # execute
        r = receiver.QueryReceiver(
            None,
            api,
            query_factory,
            queries,
            {},
            5,
            300,
            'Hourly',
            4096,
        )

        last_to_before = r.last_to_timestamp

        # pretend it's 10 minutes from now to ensure this is different from
        # the timestamp calculated during object creation
        _now = datetime.utcnow() + timedelta(minutes=10)

        r.slide_time_range()

        # verify
        last_to_after = r.last_to_timestamp

        self.assertNotEqual(last_to_after, last_to_before)
