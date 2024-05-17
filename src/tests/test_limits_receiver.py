from datetime import datetime
import unittest


from . import \
    ApiStub, \
    SessionStub
from newrelic_logging import \
    config as mod_config, \
    LoginException, \
    SalesforceApiException, \
    util
from newrelic_logging.limits import receiver


class TestLimitsReceiver(unittest.TestCase):
    def test_export_limits_raises_login_exception_if_list_limits_does(self):
        '''
        export_limits() raises a LoginException if api.list_limits() does
        given: an api instance
        and given: an http session
        when: export_limits() is called
        then: call api.list_limits() with the given session and no api version
        and when: api.list_limits() raises a LoginException
        then: raise a LoginException
        '''

        # setup
        api = ApiStub(raise_login_error=True)
        session = SessionStub()

        # execute / verify
        with self.assertRaises(LoginException) as _:
            _ = receiver.export_limits(api, session)

    def test_export_limits_raises_salesforce_exception_if_list_limits_does(self):
        '''
        export_limits() raises a SalesforceApiException if api.list_limits() does
        given: an api instance
        and given: an http session
        when: export_limits() is called
        then: call api.list_limits() with the given session and no api version
        and when: api.list_limits() raises a SalesforceApiException
        then: raise a SalesforceApiException
        '''

        # setup
        api = ApiStub(raise_error=True)
        session = SessionStub()

        # execute / verify
        with self.assertRaises(SalesforceApiException) as _:
            _ = receiver.export_limits(api, session)


    def test_export_limits_calls_list_limits_api_and_returns_result(self):
        '''
        export_limits() calls api.list_limits() with the given session and no api version and returns the result
        given: an api instance
        and given: an http session
        when: export_limits() is called
        then: call api.list_limits() with the given session and no api version
        and: return the result
        '''

        # setup
        api = ApiStub(limits_result={ 'Foo': { 'Max': 50, 'Remaining': 2 } })
        session = SessionStub()

        # execute
        limits = receiver.export_limits(api, session)

        # verify
        self.assertIsNotNone(limits)
        self.assertTrue('Foo' in limits)
        foo = limits['Foo']
        self.assertTrue('Max' in foo)
        foo['Max'] = 50
        self.assertTrue('Remaining' in foo)
        foo['Remaining'] = 2

    def test_get_limit_names_returns_names_from_options_when_exists(self):
        '''
        get_limit_names() returns the 'names' attributes from the given limits options when it exists
        given: a set of limits options from the instance configuration
        and given: the result of export_limits()
        when: get_limit_names() is called
        and when: the 'names' attribute is in the set of limits options
        then: return the value of the 'names' attribute
        '''

        # setup
        limits_options = mod_config.Config({ 'names': [ 'Foo', 'Bar' ]})
        limits = {
            'Foo': { 'Max': 50, 'Remaining': 3 },
            'Bar': { 'Max': 300, 'Remaining': 10 },
        }

        # execute
        names = receiver.get_limit_names(limits_options, limits)

        # verify
        self.assertEqual(names, [ 'Foo', 'Bar' ])

    def test_get_limit_names_returns_limit_names_when_names_not_in_limits_options(self):
        '''
        get_limit_names() returns the list of all limit names from the result of export_limits() when the 'names' attributes is not in the given limits options
        given: a set of limits options from the instance configuration
        and given: the result of export_limits()
        when: get_limit_names() is called
        and when: the 'names' attribute is not in the set of limits options
        then: return the value of list of all keys in the export_limits() result
        '''

        # setup
        limits_options = mod_config.Config({})
        limits = {
            'Foo': { 'Max': 50, 'Remaining': 3 },
            'Bar': { 'Max': 300, 'Remaining': 10 },
            'Beep': { 'Max': 1, 'Remaining': 1 },
            'Boop': { 'Max': 1024, 'Remaining': 256 },
        }

        # execute
        names = receiver.get_limit_names(limits_options, limits)

        # verify
        self.assertEqual(names, [ 'Foo', 'Bar', 'Beep', 'Boop' ])

    def test_build_attributes_returns_name_only_given_no_max_or_remaining(self):
        '''
        build_attributes() returns a dict containing only a name attribute when there are no Max or Remaining attributes in the given limit dict
        given: a set of limits options from the instance configuration
        and given: the result of export_limits()
        and given: a limit name
        when: build_attributes() is called
        and when: the limit for the given limit name does not have Max or Remaining attributes
        then: return a dict with the limit name only
        '''

        # setup
        config = mod_config.Config({})
        limits = {
            'Foo': { 'Max': 50, 'Remaining': 3 },
            'Bar': { 'Max': 300, 'Remaining': 10 },
            'Beep': { 'Max': 1, 'Remaining': 1 },
            'Boop': {},
        }

        # execute
        attrs = receiver.build_attributes(config, limits, 'Boop')

        # verify
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'Boop')
        self.assertFalse('Max' in attrs)
        self.assertFalse('Remaining' in attrs)
        self.assertFalse('Used' in attrs)

    def test_build_attributes_returns_name_and_max_given_no_remaining(self):
        '''
        build_attributes() returns a dict containing only name and Max attributes when there is no Remaining attribute in the given limit dict
        given: a set of limits options from the instance configuration
        and given: the result of export_limits()
        and given: a limit name
        when: build_attributes() is called
        and when: the limit for the given limit name has a Max attribute
        and when: the limit for the given limit name does not have a Remaining attribute
        then: return a dict with the limit name and a Max attribute
        '''

        # setup
        config = mod_config.Config({})
        limits = {
            'Foo': { 'Max': 50, 'Remaining': 3 },
            'Bar': { 'Max': 300, 'Remaining': 10 },
            'Beep': { 'Max': 1, 'Remaining': 1 },
            'Boop': { 'Max': 20 },
        }

        # execute
        attrs = receiver.build_attributes(config, limits, 'Boop')

        # verify
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'Boop')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 20)
        self.assertFalse('Remaining' in attrs)
        self.assertFalse('Used' in attrs)

    def test_build_attributes_returns_name_and_remaining_given_no_max(self):
        '''
        build_attributes() returns a dict containing only name and Remaining attributes when there is no Max attribute in the given limit dict
        given: a set of limits options from the instance configuration
        and given: the result of export_limits()
        and given: a limit name
        when: build_attributes() is called
        and when: the limit for the given limit name has a Remaining attribute
        and when: the limit for the given limit name does not have a Max attribute
        then: return a dict with the limit name and a Remaining attribute
        '''

        # setup
        config = mod_config.Config({})
        limits = {
            'Foo': { 'Max': 50, 'Remaining': 3 },
            'Bar': { 'Max': 300, 'Remaining': 10 },
            'Beep': { 'Max': 1, 'Remaining': 1 },
            'Boop': { 'Remaining': 10 },
        }

        # execute
        attrs = receiver.build_attributes(config, limits, 'Boop')

        # verify
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'Boop')
        self.assertFalse('Max' in attrs)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 10)
        self.assertFalse('Used' in attrs)

    def test_build_attributes_returns_name_and_max_and_remaining_and_used(self):
        '''
        build_attributes() returns a dict containing the name, Max, and Remaining attributes when both Max and Remaining exist in the given limit dict
        given: a set of limits options from the instance configuration
        and given: the result of export_limits()
        and given: a limit name
        when: build_attributes() is called
        and when: the limit for the given limit name has a Remaining attribute
        and when: the limit for the given limit name has a Max attribute
        then: return a dict with the limit name, a Max attribute, a Remaining attribute,
            and a Used attribute
        '''

        # setup
        config = mod_config.Config({})
        limits = {
            'Foo': { 'Max': 50, 'Remaining': 3 },
            'Bar': { 'Max': 300, 'Remaining': 10 },
            'Beep': { 'Max': 1, 'Remaining': 1 },
            'Boop': { 'Remaining': 10 },
        }

        # execute
        attrs = receiver.build_attributes(config, limits, 'Foo')

        # verify
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'Foo')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 50)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 3)
        self.assertTrue('Used' in attrs)
        self.assertEqual(attrs['Used'], 47)

    def test_build_attributes_returns_default_event_type_given_no_event_type_option(self):
        '''
        build_attributes() returns a dict containing a limit with the default event type given no event type option is specified in the config
        given: a set of limits options from the instance configuration
        and given: the result of export_limits()
        and given: a limit name
        when: build_attributes() is called
        and when: the event_type option is not set in the limits options
        then: return a dict with the limit name, a Max attribute, a Remaining attribute,
            a Used attribute, and the default EVENT_TYPE.
        '''

        # setup
        config = mod_config.Config({})
        limits = {
            'Foo': { 'Max': 50, 'Remaining': 3 },
        }

        # execute
        attrs = receiver.build_attributes(config, limits, 'Foo')

        # verify
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'Foo')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 50)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 3)
        self.assertTrue('Used' in attrs)
        self.assertEqual(attrs['Used'], 47)
        self.assertTrue('EVENT_TYPE' in attrs)
        self.assertEqual(attrs['EVENT_TYPE'], 'SalesforceOrgLimit')

    def test_build_attributes_returns_custom_event_type_given_event_type_option(self):
        '''
        build_attributes() returns a dict containing a limit with a custom event type given an event type option is specified in the config
        given: a set of limits options from the instance configuration
        and given: the result of export_limits()
        and given: a limit name
        when: build_attributes() is called
        and when: the event_type option is set in the limits options
        then: return a dict with the limit name, a Max attribute, a Remaining attribute,
            a Used attribute, and the custom EVENT_TYPE.
        '''

        # setup
        config = mod_config.Config({ 'event_type': 'CustomSFOrgLimit' })
        limits = {
            'Foo': { 'Max': 50, 'Remaining': 3 },
        }

        # execute
        attrs = receiver.build_attributes(config, limits, 'Foo')

        # verify
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'Foo')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 50)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 3)
        self.assertTrue('Used' in attrs)
        self.assertEqual(attrs['Used'], 47)
        self.assertTrue('EVENT_TYPE' in attrs)
        self.assertEqual(attrs['EVENT_TYPE'], 'CustomSFOrgLimit')

    def test_transform_limits_yields_no_results_given_no_matching_limit_names(self):
        '''
        transform_limits() yields no results when the calculated set of limit names are not part of the export_limits() result
        given: the result of export_limits()
        and given: a set of limits options from the instance configuration
        when: transform_limits() is called
        and when: the calculated set of limit names do not match any limit names in the export_limits() result
        then: yield no results
        '''
        # setup
        config = mod_config.Config({ 'names': [ 'Beep', 'Boop' ]})
        limits = {
            'Foo': { 'Max': 50, 'Remaining': 3 },
            'Bar': { 'Max': 300, 'Remaining': 10 },
        }

        # execute
        iter = receiver.transform_limits(config, limits)

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 0)

    def test_transform_limits_yields_results_given_matching_limit_names(self):
        '''
        transform_limits() yields results of all limits in the export_limits() result with a matching name in the calculated set of limit names
        given: the result of export_limits()
        and given: a set of limits options from the instance configuration
        when: transform_limits() is called
        and when: there are limits in the export_limits() result with matching names in the calculated set of limit names
        then: yield no results
        '''
        # setup
        __now = datetime.now()

        def _now():
            nonlocal __now
            return __now

        util._NOW = _now

        config = mod_config.Config({})
        limits = {
            'Foo': { 'Max': 50, 'Remaining': 3 },
            'Bar': { 'Max': 300, 'Remaining': 10 },
        }

        # execute
        iter = receiver.transform_limits(config, limits)

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 2)
        l = logs[0]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'Salesforce Org Limit: Foo')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'Foo')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 50)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 3)
        self.assertTrue('timestamp' in l)
        self.assertEqual(l['timestamp'], util.get_timestamp())

        l = logs[1]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'Salesforce Org Limit: Bar')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'Bar')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 300)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 10)
        self.assertTrue('timestamp' in l)
        self.assertEqual(l['timestamp'], util.get_timestamp())

    def test_limits_receiver_execute_yields_no_results_when_no_options(self):
        '''
        LimitsReceiver.execute() yields no results when the limits options is None (when there is no limits config in the instance config)
        given: an API instance
        and given: a set of limits options
        and given: an http session
        when: LimitsReceiver.execute() is called
        and when: the set of limits options is None
        then: yield no results
        '''

        # setup
        api = ApiStub(limits_result={
            'Foo': { 'Max': 50, 'Remaining': 2 },
            'Bar': { 'Max': 300, 'Remaining': 10 },
        })
        limits_options = None
        session = SessionStub()

        # execute
        r = receiver.LimitsReceiver(api, limits_options)
        iter = r.execute(session)

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 0)

    def test_limits_receiver_execute_yields_all_results_given_limits_options(self):
        '''
        LimitsReceiver.execute() yields all results of transform_limits() when the limits options is not None
        given: an API instance
        and given: a set of limits options
        and given: an http session
        when: LimitsReceiver.execute() is called
        and when: the set of limits options is not None
        then: yield all results of transform_limits()
        '''

        # setup
        api = ApiStub(limits_result={
            'Foo': { 'Max': 50, 'Remaining': 2 },
            'Bar': { 'Max': 300, 'Remaining': 10 },
        })
        limits_options = {}
        session = SessionStub()

        # execute
        r = receiver.LimitsReceiver(api, limits_options)
        iter = r.execute(session)

        logs = []
        for log in iter:
            logs.append(log)

        # verify
        self.assertEqual(len(logs), 2)
        l = logs[0]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'Salesforce Org Limit: Foo')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'Foo')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 50)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 2)
        self.assertTrue('timestamp' in l)
        self.assertEqual(l['timestamp'], util.get_timestamp())

        l = logs[1]
        self.assertTrue('message' in l)
        self.assertEqual(l['message'], 'Salesforce Org Limit: Bar')
        self.assertTrue('attributes' in l)
        attrs = l['attributes']
        self.assertTrue('name' in attrs)
        self.assertEqual(attrs['name'], 'Bar')
        self.assertTrue('Max' in attrs)
        self.assertEqual(attrs['Max'], 300)
        self.assertTrue('Remaining' in attrs)
        self.assertEqual(attrs['Remaining'], 10)
        self.assertTrue('timestamp' in l)
        self.assertEqual(l['timestamp'], util.get_timestamp())

    def test_limits_receiver_raises_login_exception_if_export_limits_does(self):
        '''
        LimitsReceiver.execute() raises LoginException if export_limits() does
        given: an API instance
        and given: a set of limits options
        and given: an http session
        when: LimitsReceiver.execute() is called
        and when: export_limits() raises a LoginException
        then: raise a LoginException
        '''

        # setup
        api = ApiStub(raise_login_error=True)
        limits_options = {}
        session = SessionStub()

        # execute/verify
        r = receiver.LimitsReceiver(api, limits_options)

        with self.assertRaises(LoginException) as _:
            iter = r.execute(session)
            # Have to use next to cause the generator to execute the function
            # else get_log_file() won't get executed and our stub won't have
            # a chance to throw the fake exception.
            next(iter)

    def test_limits_receiver_raises_salesforce_exception_if_export_limits_does(self):
        '''
        LimitsReceiver.execute() raises SalesforceApiException if export_limits() does
        given: an API instance
        and given: a set of limits options
        and given: an http session
        when: LimitsReceiver.execute() is called
        and when: export_limits() raises a SalesforceApiException
        then: raise a SalesforceApiException
        '''

        # setup
        api = ApiStub(raise_error=True)
        limits_options = {}
        session = SessionStub()

        # execute/verify
        r = receiver.LimitsReceiver(api, limits_options)

        with self.assertRaises(SalesforceApiException) as _:
            iter = r.execute(session)
            # Have to use next to cause the generator to execute the function
            # else get_log_file() won't get executed and our stub won't have
            # a chance to throw the fake exception.
            next(iter)
