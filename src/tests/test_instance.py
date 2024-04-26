import unittest


from . import \
    ApiStub, \
    AuthenticatorStub, \
    NewRelicApiException, \
    PipelineStub, \
    SessionStub
from newrelic_logging import \
    config as mod_config, \
    LoginException, \
    instance, \
    SalesforceApiException


class TestInstance(unittest.TestCase):
    def test_harvest_raises_login_exception_if_authenticate_does(self):
        '''
        harvest() raises a LoginException if api.authenticate() does
        given: an instance name
        and given: an instance config
        and given: an API instance
        and given: a pipeline
        and given: an http session
        when: harvest() is called
        and when: api.authenticate() raises a LoginException
        then: raise a LoginException
        '''

        # setup
        api = ApiStub(raise_login_error=True)
        p = PipelineStub()
        session = SessionStub()

        # execute/verify
        inst = instance.Instance(
            'my_instance',
            api,
            p,
        )

        with self.assertRaises(LoginException) as _:
            inst.harvest(session)

    def test_harvest_raises_salesforce_exception_if_pipeline_execute_does(self):
        '''
        harvest() raises a SalesforceApiException if pipeline.execute() does
        given: an instance name
        and given: an instance config
        and given: an API instance
        and given: a pipeline
        and given: an http session
        when: harvest() is called
        and when: pipeline.execute() raises a SalesforceApiException
        then: raise a LoginException
        '''

        # setup
        api = ApiStub(authenticator=AuthenticatorStub())
        p = PipelineStub(raise_error=True)
        session = SessionStub()

        # execute/verify
        inst = instance.Instance(
            'my_instance',
            api,
            p,
        )

        with self.assertRaises(SalesforceApiException) as _:
            inst.harvest(session)

    def test_harvest_raises_newrelic_exception_if_pipeline_execute_does(self):
        '''
        harvest() raises a NewRelicApiException if pipeline.execute() does
        given: an instance name
        and given: an instance config
        and given: an API instance
        and given: a pipeline
        and given: an http session
        when: harvest() is called
        and when: pipeline.execute() raises a NewRelicApiException
        then: raise a NewRelicApiException
        '''

        # setup
        api = ApiStub(authenticator=AuthenticatorStub())
        p = PipelineStub(raise_newrelic_error=True)
        session = SessionStub()

        # execute/verify
        inst = instance.Instance(
            'my_instance',
            api,
            p,
        )

        with self.assertRaises(NewRelicApiException) as _:
            inst.harvest(session)
