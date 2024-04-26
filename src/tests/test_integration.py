import unittest


from . import InstanceStub, \
    SessionStub, \
    TelemetryStub
from newrelic_logging import \
    integration, \
    CacheException, \
    LoginException, \
    NewRelicApiException, \
    SalesforceApiException


class TestIntegration(unittest.TestCase):
    def test_integration_process_telemetry_does_not_call_flush_when_empty(self):
        '''
        Integration.process_telemetry() does not call Telemetry.flush() when Telemetry.is_empty() returns True
        given: a Telemetry instance
        and given: a set of instance dicts from the configuration
        and given: an http session
        when: Integration.process_telemetry() is called
        and when: Telemetry.is_empty() returns True
        then: Telemetry.flush() is not called
        '''

        # setup
        telemetry = TelemetryStub()
        instances = [
            InstanceStub('instance_1'),
            InstanceStub('instance_2'),
        ]
        session = SessionStub()

        # execute
        i = integration.Integration(
            telemetry,
            instances,
        )

        i.process_telemetry(session)

        # verify
        self.assertFalse(telemetry.flush_called)

    def test_integration_process_telemetry_calls_flush_when_not_empty(self):
        '''
        Integration.process_telemetry() calls Telemetry.flush() when Telemetry.is_empty() returns False
        given: a Telemetry instance
        and given: a set of instance dicts from the configuration
        and given: an http session
        when: Integration.process_telemetry() is called
        and when: Telemetry.is_empty() returns False
        then: Telemetry.flush() is called
        '''

        # setup
        telemetry = TelemetryStub(empty=False)
        instances = [
            InstanceStub('instance_1'),
            InstanceStub('instance_2'),
        ]
        session = SessionStub()

        # execute
        i = integration.Integration(
            telemetry,
            instances,
        )

        i.process_telemetry(session)

        # verify
        self.assertTrue(telemetry.flush_called)

    def test_integration_run_calls_harvest_for_each_instance(self):
        '''
        Integration.run() calls the Instance.harvest() method on each instance given a set of instances
        given: a Telemetry instance
        and given: a set of instance dicts from the configuration
        when: Integration.run() is called
        then: Instance.harvest() is called on each instance
        '''

        # setup
        telemetry = TelemetryStub()
        instances = [
            InstanceStub('instance_1'),
            InstanceStub('instance_2'),
        ]

        # execute
        i = integration.Integration(
            telemetry,
            instances,
        )

        i.run()

        # verify
        self.assertTrue(instances[0].harvest_called)
        self.assertTrue(instances[1].harvest_called)

    def test_integration_run_raises_login_exception_if_instance_harvest_does(self):
        '''
        Integration.run() raises LoginException if Instance.harvest() does
        given: a Telemetry instance
        and given: a set of instance dicts from the configuration
        when: Integration.run() is called
        and when: Instance.harvest() raises a LoginException
        then: raise a LoginException
        '''

        # setup
        telemetry = TelemetryStub()
        instances = [ InstanceStub(raise_login_error=True) ]

        # execute / verify
        i = integration.Integration(
            telemetry,
            instances,
        )

        with self.assertRaises(LoginException) as _:
            i.run()

    def test_integration_run_raises_salesforce_exception_if_instance_harvest_does(self):
        '''
        Integration.run() raises SalesforceApiException if Instance.harvest() does
        given: a Telemetry instance
        and given: a set of instance dicts from the configuration
        when: Integration.run() is called
        and when: Instance.harvest() raises a SalesforceApiException
        then: raise a SalesforceApiException
        '''

        # setup
        telemetry = TelemetryStub()
        instances = [ InstanceStub(raise_error=True) ]

        # execute / verify
        i = integration.Integration(
            telemetry,
            instances,
        )

        with self.assertRaises(SalesforceApiException) as _:
            i.run()

    def test_integration_run_raises_cache_exception_if_instance_harvest_does(self):
        '''
        Integration.run() raises CacheException if Instance.harvest() does
        given: a Telemetry instance
        and given: a set of instance dicts from the configuration
        when: Integration.run() is called
        and when: Instance.harvest() raises a CacheException
        then: raise a CacheException
        '''

        # setup
        telemetry = TelemetryStub()
        instances = [ InstanceStub(raise_cache_error=True) ]

        # execute / verify
        i = integration.Integration(
            telemetry,
            instances,
        )

        with self.assertRaises(CacheException) as _:
            i.run()

    def test_integration_run_raises_newrelic_exception_if_instance_harvest_does(self):
        '''
        Integration.run() raises NewRelicApiException if Instance.harvest() does
        given: a Telemetry instance
        and given: a set of instance dicts from the configuration
        when: Integration.run() is called
        and when: Instance.harvest() raises a NewRelicApiException
        then: raise a NewRelicApiException
        '''

        # setup
        telemetry = TelemetryStub()
        instances = [ InstanceStub(raise_newrelic_error=True) ]

        # execute / verify
        i = integration.Integration(
            telemetry,
            instances,
        )

        with self.assertRaises(NewRelicApiException) as _:
            i.run()

    def test_integration_run_raises_exception_if_instance_harvest_does(self):
        '''
        Integration.run() raises an unexpected Exception if Instance.harvest() does
        given: a Telemetry instance
        and given: a set of instance dicts from the configuration
        when: Integration.run() is called
        and when: Instance.harvest() raises an unexpected Exception
        then: raise an Exception
        '''

        # setup
        telemetry = TelemetryStub()
        instances = [ InstanceStub(raise_unexpected_error=True) ]

        # execute / verify
        i = integration.Integration(
            telemetry,
            instances,
        )

        with self.assertRaises(Exception) as _:
            i.run()
