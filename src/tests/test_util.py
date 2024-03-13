import hashlib
import unittest

from newrelic_logging import util

class TestUtilities(unittest.TestCase):
    def test_is_logfile_response(self):
        '''
        given: a set of query result records
        when: the set is the empty set
        then: return true
        '''

        # execute/verify
        self.assertTrue(util.is_logfile_response([]))

        '''
        given: a set of query result records
        when: the first record in the set contains a 'LogFile' property
        then: return true
        '''

        # execute/verify
        self.assertTrue(util.is_logfile_response([
            { 'LogFile': 'example' }
        ]))

        '''
        given: a set of query result records
        when: the first record in the set does not contain a 'LogFile' property
        then: return false
        '''

        # execute/verify
        self.assertFalse(util.is_logfile_response([{}]))

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


if __name__ == '__main__':
    unittest.main()
