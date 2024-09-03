from datetime import datetime, timedelta
import hashlib
import json
import pytz
import unittest

from newrelic_logging import util

class TestUtilities(unittest.TestCase):
    def test_is_logfile_response(self):
        '''
        given: a query result record
        when: the record contains a 'LogFile' property
        then: return true
        '''

        # execute/verify
        self.assertTrue(util.is_logfile_response(
            { 'LogFile': 'example' }
        ))

        '''
        given: a query result record
        when: the record does not contain a 'LogFile' property
        then: return false
        '''

        # execute/verify
        self.assertFalse(util.is_logfile_response({}))

    def test_regenerator_yields_all_given_items_and_iter_has_no_more(self):
        '''
        regenerator() returns an iterator over items given itr has no more elements
        given: an array of items
        and given: an iterator
        when: the array is not empty
        and when: the iterator has no more elements
        and when: regenerator() is called
        then: regenerator() yields all items
        '''

        # setup
        items = [1]
        itr = iter([])

        # execute
        result = []
        for r in util.regenerator(items, itr):
            result.append(r)

        # verify
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 1)

    def test_regenerator_yields_all_given_iter_has_more_and_no_items(self):
        '''
        regenerator() returns an iterator over the elements in itr given items is empty
        given: an array of items
        and given: an iterator
        when: the array is empty
        and when: the iterator has more elements
        and when: regenerator() is called
        then: regenerator() yields all elements from the iterator
        '''

        # setup
        items = []
        itr = iter([1, 2, 3])

        # execute
        result = []
        for r in util.regenerator(items, itr):
            result.append(r)

        # verify
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 1)
        self.assertEqual(result[1], 2)
        self.assertEqual(result[2], 3)

    def test_regenerator_yields_all_given_items_and_iter_has_more(self):
        '''
        regenerator() returns an iterator over items and the elements in itr given items is not empty and itr has more elements
        given: an array of items
        and given: an iterator
        when: the array is not empty
        and when: the iterator has more elements
        and when: regenerator() is called
        then: regenerator() yields all items and all elements from the iterator
        '''

        # setup
        items = [1, 2, 3]
        itr = iter([4, 5, 6])

        # execute
        result = []
        for r in util.regenerator(items, itr):
            result.append(r)

        # verify
        self.assertEqual(len(result), 6)
        self.assertEqual(result[0], 1)
        self.assertEqual(result[1], 2)
        self.assertEqual(result[2], 3)
        self.assertEqual(result[3], 4)
        self.assertEqual(result[4], 5)
        self.assertEqual(result[5], 6)

    def test_generate_record_id(self):
        '''
        given: a set of id keys and a query result record
        when: the set of id keys is the empty set
        then: return the empty string
        '''

        # execute
        record_id = util.generate_record_id([], { 'Name': 'foo' })

        # verify
        self.assertEqual(record_id, '')

        '''
        given: a set of id keys and a query result record
        when: the set of id keys is not empty
        and when: there is some key for which the query result record does not
                  have a property
        then: an exception is raised
        '''

        # execute/verify
        with self.assertRaises(Exception):
            util.generate_record_id([ 'EventType' ], { 'Name': 'foo' })

        '''
        given: a set of id keys and a query result record
        when: the set of id keys is not empty
        and when: the query result record has a property for the key but the
                  value for that key is the empty string
        then: return the empty string
        '''

        # execute
        record_id = util.generate_record_id([ 'Name' ], { 'Name': '' })

        # verify
        self.assertEqual(record_id, '')

        '''
        given: a set of id keys and a query result record
        when: the set of id keys is not empty
        and when: the query result record has a property for the key with a
                  value that is not the emptry string
        then: return a value obtained by concatenating the values for all id
              keys and creating a sha3 256 message digest over that value
        '''

        # execute
        record_id = util.generate_record_id([ 'Name' ], { 'Name': 'foo' })

        # verify
        m = hashlib.sha3_256()
        m.update('foo'.encode('utf-8'))
        expected = m.hexdigest()

        self.assertEqual(expected, record_id)

    def test_maybe_convert_str_to_num(self):
        '''
        given: a string
        when: the string contains a valid integer
        then: the string value is converted to an integer
        '''

        # execute
        val = util.maybe_convert_str_to_num('2')

        # verify
        self.assertTrue(type(val) is int)
        self.assertEqual(val, 2)

        '''
        given: a string
        when: the string contains a valid floating point number
        then: the string value is converted to a float
        '''

        # execute
        val = util.maybe_convert_str_to_num('3.14')

        # verify
        self.assertTrue(type(val) is float)
        self.assertEqual(val, 3.14)

        '''
        given: a string
        when: the string contains neither a valid integer nor a valid floating
              point number
        then: the string value is returned
        '''

        # execute
        val = util.maybe_convert_str_to_num('not a number')

        # verify
        self.assertTrue(type(val) is str)
        self.assertEqual(val, 'not a number')

    def test_get_iso_date_with_offset(self):
        _now = datetime.utcnow()

        def _utcnow():
            nonlocal _now
            return _now

        util._UTCNOW = _utcnow

        '''
        given: a time lag and initial delay
        when: neither are specified (both default to 0)
        then: return the current time in iso format
        '''

        # setup
        val = _now.isoformat(timespec='milliseconds') + 'Z'

        # execute
        isonow = util.get_iso_date_with_offset()

        # verify
        self.assertEqual(val, isonow)

        '''
        given: a time lag and initial delay
        when: time lag is specified
        then: return the current time minus the time lag in iso format
        '''

        # setup
        time_lag_minutes = 412
        val = (_now - timedelta(minutes=time_lag_minutes)) \
            .isoformat(timespec='milliseconds') + 'Z'

        # execute
        isonow = util.get_iso_date_with_offset(
            time_lag_minutes=time_lag_minutes
        )

        # verify
        self.assertEqual(val, isonow)

        '''
        given: a time lag and initial delay
        when: initial delay is specified
        then: return the current time minus the initial delay in iso format
        '''

        # setup
        initial_delay = 678
        val = (_now - timedelta(minutes=initial_delay)) \
            .isoformat(timespec='milliseconds') + 'Z'

        # execute
        isonow = util.get_iso_date_with_offset(initial_delay=initial_delay)

        # verify
        self.assertEqual(val, isonow)

        '''
        given: a time lag and initial delay
        when: both are specified
        then: return the current time minus the sum of the time lag and initial
              delay in iso format
        '''

             # setup
        initial_delay = 678
        val = (_now - timedelta(minutes=(time_lag_minutes + initial_delay))) \
            .isoformat(timespec='milliseconds') + 'Z'

        # execute
        isonow = util.get_iso_date_with_offset(
            time_lag_minutes,
            initial_delay,
        )

        # verify
        self.assertEqual(val, isonow)

    def test_is_primitive_true_for_primitive_types(self):
        '''
        is_primitive() returns true for types considered to be "primitive" (str, int, float, bool, None)
        given: a set of "primitive" values
        when: is_primitive() is called
        then: returns True
        '''

        # setup
        vals = ('string', 100, 62.1, False, None)

        # execute / verify
        for v in vals:
            b = util.is_primitive(v)
            self.assertTrue(b)

    def test_is_primitive_false_for_non_primitive_types(self):
        '''
        is_primitive() returns false for types not considered to be "primitive"
        given: a set of "non-primitive" values
        when: is_primitive() is called
        then: returns False
        '''

        # setup
        vals = (['list'], (1, 2), { 'foo': 'bar' }, Exception())

        # execute / verify
        for v in vals:
            b = util.is_primitive(v)
            self.assertFalse(b)

    def test_process_query_result_copies_primitive_fields(self):
        '''
        process_query_result() copies all primitive fields to the new dict
        given: JSON result from an SOQL query
        when: the SOQL query result contains only primitive (non-nested) fields
        then: returns dict containing all primitive fields
        '''

        # setup
        query_result = json.loads('''{
            "Action": "PermSetFlsChanged",
            "CreatedByContext": null,
            "CreatedById": "0058W00000A7LvTQAV",
            "CreatedByIssuer": 1,
            "CreatedDate": "2023-11-30T17:33:08.000+0000",
            "DelegateUser": 2.0,
            "Display": "Changed permission set 00e1U000000XFwxQAG: field-level security for Task: Related To was changed from Read/Write to No Access",
            "Id": "0Ym7c00001RGP6MCAX",
            "ResponsibleNamespacePrefix": false,
            "Section": "Manage Users"
        }''')

        expected_result = {
            'Action': 'PermSetFlsChanged',
            'CreatedByContext': None,
            'CreatedById': '0058W00000A7LvTQAV',
            'CreatedByIssuer': 1,
            'CreatedDate': '2023-11-30T17:33:08.000+0000',
            'DelegateUser': 2.0,
            'Display': 'Changed permission set 00e1U000000XFwxQAG: field-level security for Task: Related To was changed from Read/Write to No Access',
            'Id': '0Ym7c00001RGP6MCAX',
            'ResponsibleNamespacePrefix': False,
            'Section': 'Manage Users'
        }

        # execute
        result = util.process_query_result(query_result)

        # verify
        self.assertEqual(expected_result, result)

    def test_process_query_result_flattens_and_copies_nested_fields(self):
        '''
        process_query_result() flattens all nested fields and copies them to the new dict with keys that use the syntax "field1.nestedfield1.nestedfield1" and so on
        given: JSON result from an SOQL query
        when: the SOQL query result contains primitive and nested fields
        then: returns dict containing all primitive fields
        and: contains primitives from all nested fields
        and: the keys for all nested fields use the syntax 'field1.nestedfield1', 'field2.nestedfield2.nestedfield1' and so on
        '''

        # setup
        query_result = json.loads('''{
            "Action": "PermSetFlsChanged",
            "CreatedByContext": null,
            "CreatedById": "0058W00000A7LvTQAV",
            "CreatedBy": {
                "Name": "Chetan Gupta",
                "Profile": {
                    "Name": "System Administrator"
                },
                "UserType": "Standard"
            },
            "CreatedByIssuer": null,
            "CreatedDate": "2023-11-30T17:33:08.000+0000",
            "DelegateUser": null,
            "Display": "Changed permission set 00e1U000000XFwxQAG: field-level security for Task: Related To was changed from Read/Write to No Access",
            "Id": "0Ym7c00001RGP6MCAX",
            "ResponsibleNamespacePrefix": null,
            "Section": "Manage Users"
        }''')

        expected_result = {
            'Action': 'PermSetFlsChanged',
            'CreatedBy.Name': 'Chetan Gupta',
            'CreatedBy.Profile.Name': 'System Administrator',
            'CreatedBy.UserType': 'Standard',
            'CreatedByContext': None,
            'CreatedById': '0058W00000A7LvTQAV',
            'CreatedByIssuer': None,
            'CreatedDate': '2023-11-30T17:33:08.000+0000',
            'DelegateUser': None,
            'Display': 'Changed permission set 00e1U000000XFwxQAG: field-level security for Task: Related To was changed from Read/Write to No Access',
            'Id': '0Ym7c00001RGP6MCAX',
            'ResponsibleNamespacePrefix': None,
            'Section': 'Manage Users'
        }

        # execute
        result = util.process_query_result(query_result)

        # verify
        self.assertEqual(expected_result, result)

    def test_process_query_result_ignores_attributes_fields(self):
        '''
        process_query_result() ignores all fields and nested fields named 'attributes'
        given: JSON result from an SOQL query
        when: the SOQL query result contains primitive and nested fields
        and when: the SOQL query result contains fields and nested fields named 'attributes'
        then: returns dict containing all primitive fields
        and: contains primitives from all nested fields
        and: the keys for all nested fields use the syntax 'field1.nestedfield1', 'field2.nestedfield2.nestedfield1' and so on
        and: fields and nested fields named 'attributes' are ignored
        '''

        # setup
        query_result = json.loads('''{
            "attributes": {
                "type": "SetupAuditTrail",
                "url": "/services/data/v55.0/sobjects/SetupAuditTrail/0Ym7c00001RGP6MCAX"
            },
            "Action": "PermSetFlsChanged",
            "CreatedByContext": null,
            "CreatedById": "0058W00000A7LvTQAV",
            "CreatedBy": {
                "attributes": {
                    "type": "User",
                    "url": "/services/data/v55.0/sobjects/User/0058W00000A7LvTQAV"
                },
                "Name": "Chetan Gupta",
                "Profile": {
                    "attributes": {
                        "type": "Profile",
                        "url": "/services/data/v55.0/sobjects/Profile/00e1U000001wRS1QAM"
                    },
                    "Name": "System Administrator"
                },
                "UserType": "Standard"
            },
            "CreatedByIssuer": null,
            "CreatedDate": "2023-11-30T17:33:08.000+0000",
            "DelegateUser": null,
            "Display": "Changed permission set 00e1U000000XFwxQAG: field-level security for Task: Related To was changed from Read/Write to No Access",
            "Id": "0Ym7c00001RGP6MCAX",
            "ResponsibleNamespacePrefix": null,
            "Section": "Manage Users"
        }''')

        expected_result = {
            'Action': 'PermSetFlsChanged',
            'CreatedBy.Name': 'Chetan Gupta',
            'CreatedBy.Profile.Name': 'System Administrator',
            'CreatedBy.UserType': 'Standard',
            'CreatedByContext': None,
            'CreatedById': '0058W00000A7LvTQAV',
            'CreatedByIssuer': None,
            'CreatedDate': '2023-11-30T17:33:08.000+0000',
            'DelegateUser': None,
            'Display': 'Changed permission set 00e1U000000XFwxQAG: field-level security for Task: Related To was changed from Read/Write to No Access',
            'Id': '0Ym7c00001RGP6MCAX',
            'ResponsibleNamespacePrefix': None,
            'Section': 'Manage Users'
        }

        # execute
        result = util.process_query_result(query_result)

        # verify
        self.assertEqual(expected_result, result)

    def test_process_query_result_ignores_non_dict_structured_fields(self):
        '''
        process_query_result() ignores all fields and nested fields that are neither "primitive" nor type dict
        given: JSON result from an SOQL query
        when: the SOQL query result contains primitive and nested fields
        and when: the SOQL query result contains fields and nested fields that are neither "primitive" nor type dict
        then: returns dict containing all primitive fields
        and: contains primitives from all nested fields
        and: the keys for all nested fields use the syntax 'field1.nestedfield1', 'field2.nestedfield2.nestedfield1' and so on
        and: fields and nested fields that are neither "primitive" nor type dict are ignored
        '''

        # setup
        query_result = json.loads('''{
            "Action": "PermSetFlsChanged",
            "CreatedByContext": null,
            "CreatedById": "0058W00000A7LvTQAV",
            "CreatedByIssuer": null,
            "CreatedDate": "2023-11-30T17:33:08.000+0000",
            "DelegateUser": null,
            "Display": "Changed permission set 00e1U000000XFwxQAG: field-level security for Task: Related To was changed from Read/Write to No Access",
            "Id": "0Ym7c00001RGP6MCAX",
            "ResponsibleNamespacePrefix": null,
            "Section": "Manage Users",
            "RandomNested": {
                "RandomNestedArray": ["beep", "boop"]
            },
            "RandomArray": ["foo", "bar"]
        }''')

        expected_result = {
            'Action': 'PermSetFlsChanged',
            'CreatedByContext': None,
            'CreatedById': '0058W00000A7LvTQAV',
            'CreatedByIssuer': None,
            'CreatedDate': '2023-11-30T17:33:08.000+0000',
            'DelegateUser': None,
            'Display': 'Changed permission set 00e1U000000XFwxQAG: field-level security for Task: Related To was changed from Read/Write to No Access',
            'Id': '0Ym7c00001RGP6MCAX',
            'ResponsibleNamespacePrefix': None,
            'Section': 'Manage Users'
        }

        # execute
        result = util.process_query_result(query_result)

        # verify
        self.assertEqual(expected_result, result)

    def test_get_timestamp_returns_current_posix_ms_as_int(self):
        '''
        get_timestamp() returns current posix time in ms as an integer
        given: a date string
        when: the date string is None
        then: returns the current posix time in ms as an integer
        '''

        # setup

        __now = datetime.now()

        def _now():
            nonlocal __now
            return __now

        util._NOW = _now

        expected = int(__now.timestamp() * 1000)

        # execute
        timestamp = util.get_timestamp()

        # verify
        self.assertEqual(expected, timestamp)

    def test_get_timestamp_returns_posix_ms_as_int_for_date_string(self):
        '''
        get_timestamp() returns the posix time in ms as an integer for the time specified in the date string
        given: a date string
        when: the date string is not None
        and when: the date string is of the form %Y-%m-%dT%H:%M:%S.%f%z
        then: returns the posix time in ms as an integer for the date string
        '''

        # setup
        date_string = '2024-03-11T00:00:00.000+0000'
        time = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%f%z')
        expected = int(time.timestamp() * 1000)

        # execute
        timestamp = util.get_timestamp(date_string)

        # verify
        self.assertEqual(expected, timestamp)

    def test_get_log_line_timestamp_returns_now_when_missing_timestamp_attribute(self):
        _now = datetime.utcnow()

        def _utcnow():
            nonlocal _now
            return _now

        util._UTCNOW = _utcnow

        '''
        get_log_line_timestamp() returns a timestamp representing the current time when no TIMESTAMP attribute is found in the log line
        given: a log line
        when: get_log_line_timestamp() is called
        and when: there is no TIMESTAMP attribute
        then: return the current timestamp
        '''

        # setup
        now = _now.replace(microsecond=0)

        # execute
        ts = util.get_log_line_timestamp({})

        # verify
        self.assertEqual(now.timestamp(), ts)

    def test_get_log_line_timestamp_returns_timestamp_from_attribute(self):
        '''
        get_log_line_timestamp() returns a timestamp representing TIMESTAMP attribute when a TIMESTAMP attribute is found in the log line
        given: a log line
        when: get_log_line_timestamp() is called
        when: there is a TIMESTAMP attribute
        then: parse the string in the format YYYYMMDDHHmmss.FFF and return
              the representative timestamp
        '''

        # setup
        now = datetime.utcnow().replace(microsecond=0)
        epoch = now.strftime('%Y%m%d%H%M%S.%f')

        # execute
        ts1 = pytz.utc.localize(now).replace(microsecond=0).timestamp()
        ts2 = util.get_log_line_timestamp({ 'TIMESTAMP': epoch })

        # verify
        self.assertEqual(ts1, ts2)


if __name__ == '__main__':
    unittest.main()
