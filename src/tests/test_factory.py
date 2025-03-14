import os
import unittest
from unittest.mock import patch

from . import \
    AuthenticatorStub, \
    ApiStub, \
    BackendStub, \
    BackendFactoryStub, \
    DataCacheStub, \
    FactoryStub, \
    InstanceStub, \
    NewRelicStub, \
    PipelineStub, \
    ReceiverStub, \
    TelemetryStub
from newrelic_logging import \
    api as mod_api, \
    cache, \
    config as mod_config, \
    ConfigException, \
    DataFormat, \
    factory, \
    instance as mod_inst, \
    integration, \
    newrelic, \
    NewRelicApiException, \
    pipeline, \
    telemetry as mod_telemetry


class TestFactory(unittest.TestCase):
    def test_new_backend_factory_returns_backend_factory(self):
        '''
        new_backend_factory() returns a backend factory
        when: new_backend_factory() is called
        then: return a BackendFactory instance
        '''

        # execute
        f = factory.Factory()
        backend_factory = f.new_backend_factory()

        # verify
        self.assertIsNotNone(backend_factory)
        self.assertEqual(type(backend_factory), cache.BackendFactory)

    def test_new_data_cache_returns_none_if_disabled(self):
        '''
        new_data_cache() returns None if cache disabled
        given: an instance configuration
        and given: a backend factory
        when: new_data_cache() is called
        and when: cache_enabled is False in instance configuration
        then: None is returned
        '''

        # setup
        instance_config = mod_config.Config({ 'cache_enabled': 'false' })
        backend_factory = BackendFactoryStub()

        # execute
        f = factory.Factory()
        data_cache = f.new_data_cache(instance_config, backend_factory)

        # verify
        self.assertIsNone(data_cache)

    def test_new_data_cache_returns_data_cache_with_backend_if_enabled(self):
        '''
        new_data_cache() returns DataCache instance with backend from specified backend factory if cache enabled
        given: an instance configuration
        and given: a backend factory
        when: new_data_cache() is called
        and when: cache_enabled is True in instance configuration
        then: a DataCache is returned with the a backend from the specified
            backend factory
        '''

        # setup
        instance_config = mod_config.Config({ 'cache_enabled': 'true' })
        backend_factory = BackendFactoryStub()

        # execute
        f = factory.Factory()
        data_cache = f.new_data_cache(instance_config, backend_factory)

        # verify
        self.assertIsNotNone(data_cache)
        self.assertTrue(type(data_cache.backend) is BackendStub)

    def test_new_data_cache_returns_data_cache_with_backend_and_expiry_days_from_config_if_enabled(self):
        '''
        new_data_cache() returns DataCache instance with backend from specified backend factory and the expiry days value from the config if cache enabled
        given: an instance configuration
        and given: a backend factory
        when: new_data_cache() is called
        and when: cache_enabled is True in instance configuration
        and when: redis.expire_days is specified in instance configuration
        then: return a DataCache with a backend from the specified backend factory
        and: the expiry set to the value from the instance config.
        '''

        # setup
        instance_config = mod_config.Config({
            'cache_enabled': 'true',
            'redis': {
                'expire_days': 300,
            }
        })
        backend_factory = BackendFactoryStub()

        # execute
        f = factory.Factory()
        data_cache = f.new_data_cache(instance_config, backend_factory)

        # verify
        self.assertIsNotNone(data_cache)
        self.assertTrue(type(data_cache.backend) is BackendStub)
        self.assertEqual(data_cache.expiry, 300)

    def test_new_data_cache_raises_if_backend_factory_does(self):
        '''
        new_data_cache() raises CacheException if backend factory does
        given: an instance configuration
        and given: a backend factory
        when: new_data_cache() is called
        and when: backend factory new_backend() raises an exception
        then: a CacheException is raised
        '''

        # setup
        instance_config = mod_config.Config({ 'cache_enabled': 'true' })
        backend_factory = BackendFactoryStub(raise_error=True)

        # execute / verify
        f = factory.Factory()

        with self.assertRaises(cache.CacheException):
            _ = f.new_data_cache(instance_config, backend_factory)

    def test_new_authenticator_raises_config_exception_given_no_token_url(self):
        '''
        new_authenticator() raises a ConfigException when no token URL is found in the instance config or the environment
        given: an instance configuration
        and given: a data cache
        when: new_authenticator() is called
        and when: no token URL is found in the instance config or the environment
        then: raise a ConfigException
        '''

        # setup
        config = mod_config.Config({})

        # execute / verify
        f = factory.Factory()

        with self.assertRaises(ConfigException) as _:
            f.new_authenticator(config, None)

    def test_new_authenticator_returns_new_authenticator_from_config(self):
        '''
        new_authenticator() returns a new Authenticator configured from the instance config when the 'auth' property exists
        given: an instance configuration
        and given: a data cache
        when: new_authenticator() is called
        and when: the data cache is None
        and when: the 'auth' property exists in the instance configuration
        then: return a new Authenticator configured from the 'auth' property
        '''

        # setup
        config = mod_config.Config({
            'token_url': 'https://my.salesforce.test',
            'auth': {
                'grant_type': 'password',
                'client_id': '12345',
                'client_secret': '56789',
                'username': 'foo',
                'password': 'beepboop'
            }
        })

        # execute
        f = factory.Factory()
        authenticator = f.new_authenticator(config, None)

        # verify
        self.assertEqual(authenticator.token_url, 'https://my.salesforce.test')
        self.assertIsNone(authenticator.data_cache)

        auth_data = authenticator.auth_data

        self.assertIsNotNone(auth_data)
        self.assertTrue('grant_type' in auth_data)
        self.assertEqual(auth_data['grant_type'], 'password')
        self.assertTrue('client_id' in auth_data)
        self.assertEqual(auth_data['client_id'], '12345')
        self.assertTrue('client_secret' in auth_data)
        self.assertEqual(auth_data['client_secret'], '56789')
        self.assertTrue('username' in auth_data)
        self.assertEqual(auth_data['username'], 'foo')
        self.assertTrue('password' in auth_data)
        self.assertEqual(auth_data['password'], 'beepboop')

    @patch.dict(os.environ, {
        'SF_TOKEN_URL': 'https://my.salesforce.test',
        'SF_GRANT_TYPE': 'password',
        'SF_CLIENT_ID': 'ABCDEF',
        'SF_CLIENT_SECRET': 'GHIJKL',
        'SF_USERNAME': 'bar',
        'SF_PASSWORD': 'bizzbuzz',
    })
    def test_new_authenticator_returns_new_authenticator_from_env(self):
        '''
        new_authenticator() returns a new Authenticator configured from the instance config when the 'auth' property exists
        given: an instance configuration
        and given: a data cache
        when: new_authenticator() is called
        and when: the data cache is None
        and when: the 'auth' property exists in the instance configuration
        then: return a new Authenticator configured from the 'auth' property
        '''

        # setup
        config = mod_config.Config({})

        # execute
        f = factory.Factory()
        authenticator = f.new_authenticator(config, None)

        # verify
        self.assertEqual(authenticator.token_url, 'https://my.salesforce.test')
        self.assertIsNone(authenticator.data_cache)

        auth_data = authenticator.auth_data

        self.assertIsNotNone(auth_data)
        self.assertTrue('grant_type' in auth_data)
        self.assertEqual(auth_data['grant_type'], 'password')
        self.assertTrue('client_id' in auth_data)
        self.assertEqual(auth_data['client_id'], 'ABCDEF')
        self.assertTrue('client_secret' in auth_data)
        self.assertEqual(auth_data['client_secret'], 'GHIJKL')
        self.assertTrue('username' in auth_data)
        self.assertEqual(auth_data['username'], 'bar')
        self.assertTrue('password' in auth_data)
        self.assertEqual(auth_data['password'], 'bizzbuzz')

    def test_new_authenticator_returns_new_authenticator_with_given_data_cache(self):
        '''
        new_authenticator() returns a new Authenticator configured with the given data cache
        given: an instance configuration
        and given: a data cache
        when: new_authenticator() is called
        and when: the data cache is not None
        then: return a new Authenticator with the given data cache
        '''

        # setup
        config = mod_config.Config({
            'token_url': 'https://my.salesforce.test',
            'auth': {
                'grant_type': 'password',
                'client_id': '12345',
                'client_secret': '56789',
                'username': 'foo',
                'password': 'beepboop'
            }
        })
        data_cache = DataCacheStub()

        # execute
        f = factory.Factory()
        authenticator = f.new_authenticator(config, data_cache)

        # verify
        self.assertEqual(authenticator.data_cache, data_cache)

    def test_new_api_returns_api_with_given_authenticator_and_api_version(self):
        '''
        new_api() returns an Api instance with the given authenticator instance and api version
        given: an authenticator
        and given: an api version
        when: new_api() is called
        then: return an Api instance with the given authenticator instance
            and api version
        '''

        # setup
        authenticator = AuthenticatorStub()
        api_ver = '55.0'

        # execute
        f = factory.Factory()
        api = f.new_api(authenticator, api_ver)

        # verify
        self.assertIsNotNone(api)
        self.assertEqual(type(api), mod_api.Api)
        self.assertEqual(api.authenticator, authenticator)
        self.assertEqual(api.api_ver, api_ver)

    def test_new_pipeline_returns_pipeline_with_given_values(self):
        '''
        new_pipeline() returns a new Pipeline instance with the given value
        given: an instance configuration
        and given: a data cache
        and given: a NewRelic instance
        and given: a data format
        and given: labels
        and given: a numeric fields list set
        when: new_pipeline() is called
        then: returns a new Pipeline configured with the given values
        '''

        # setup
        instance_config = mod_config.Config({})
        data_cache = DataCacheStub({})
        new_relic = NewRelicStub()
        labels = { 'foo': 'bar' }
        numeric_fields_list = set(['foo', 'bar'])

        # execute
        f = factory.Factory()
        p = f.new_pipeline(
            instance_config,
            data_cache,
            new_relic,
            DataFormat.LOGS,
            labels,
            numeric_fields_list,
        )

        # verify
        self.assertIsNotNone(p)
        self.assertEqual(type(p), pipeline.Pipeline)
        self.assertEqual(p.config, instance_config)
        self.assertEqual(p.data_cache, data_cache)
        self.assertEqual(p.new_relic, new_relic)
        self.assertEqual(p.data_format, DataFormat.LOGS)
        self.assertEqual(p.labels, labels)
        self.assertEqual(p.numeric_fields_list, numeric_fields_list)

    def test_new_instance_returns_instance_with_given_values(self):
        '''
        new_instance() returns a new Instance with the given values
        given: a factory
        and given: an instance name
        and given: an instance config
        and given: a data format
        and given: a NewRelic instance
        and given: a list of receiver creation functions
        and given: a dict of labels
        and given: a numeric fields set
        when: new_instance() is called
        then: return an Instance instance with an instance name and a properly
            configured Api instance and Pipeline instance
        '''

        # setup
        receiver_1 = None
        receiver_1_called = False
        receiver_2 = None
        receiver_2_called = False

        def new_receiver_1(
            instance_config: mod_config.Config,
            data_cache: cache.DataCache,
            api: mod_api.Api,
        ):
            nonlocal receiver_1_called
            nonlocal receiver_1
            receiver_1_called = True
            receiver_1 = ReceiverStub(
                instance_config=instance_config,
                data_cache=data_cache,
                api=api,
            )
            return receiver_1

        def new_receiver_2(
            instance_config: mod_config.Config,
            data_cache: cache.DataCache,
            api: mod_api.Api,
        ):
            nonlocal receiver_2_called
            nonlocal receiver_2
            receiver_2_called = True
            receiver_2 = ReceiverStub(
                instance_config=instance_config,
                data_cache=data_cache,
                api=api,
            )
            return receiver_2

        instance_config = mod_config.Config({
            'cache_enabled': True,
        })
        data_cache = DataCacheStub()
        backend_factory = BackendFactoryStub()
        authenticator = AuthenticatorStub()
        api = ApiStub()
        p = PipelineStub()
        new_relic = NewRelicStub()

        # execute
        f = factory.Factory()
        fs = FactoryStub(
            data_cache=data_cache,
            backend_factory=backend_factory,
            authenticator=authenticator,
            api=api,
            pipeline=p,
            new_relic=new_relic
        )

        instance = f.new_instance(
            fs,
            'test-inst-1',
            instance_config,
            DataFormat.LOGS,
            new_relic,
            [new_receiver_1, new_receiver_2],
            { 'foo': 'bar' },
            set(),
        )

        # verify
        self.assertIsNotNone(instance)
        self.assertEqual(type(instance), mod_inst.Instance)
        self.assertTrue(hasattr(instance, 'name'))
        self.assertEqual(instance.name, 'test-inst-1')
        self.assertTrue(hasattr(instance, 'api'))
        self.assertEqual(instance.api, api)
        self.assertTrue(hasattr(instance, 'pipeline'))
        self.assertEqual(instance.pipeline, p)
        self.assertTrue(receiver_1_called)
        self.assertTrue(receiver_2_called)
        self.assertEqual(len(instance.pipeline.receivers), 2)
        r = instance.pipeline.receivers[0]
        self.assertEqual(r, receiver_1)
        self.assertEqual(r.instance_config, instance_config)
        self.assertEqual(r.data_cache, data_cache)
        self.assertEqual(r.api, api)
        r = instance.pipeline.receivers[1]
        self.assertEqual(r, receiver_2)
        self.assertEqual(r.instance_config, instance_config)
        self.assertEqual(r.data_cache, data_cache)
        self.assertEqual(r.api, api)

    def test_new_integration_raises_config_exception_given_missing_instances(self):
        '''
        new_integration() raises a ConfigException given an integration configuration with no 'instances' property
        given: a factory
        and given: an integration configuration
        and given: a list of receiver creation functions
        and given: a numeric fields set
        when: new_instance() is called
        and when: the integration configuration does not contain an 'instances'
            property
        then: raise a ConfigException
        '''

        # setup
        config = mod_config.Config({})

        # execute / verify
        with self.assertRaises(ConfigException) as _:
            f = factory.Factory()
            fs = FactoryStub()

            _ = f.new_integration(fs, config, [], set())

    def test_new_integration_raises_config_exception_given_no_instances(self):
        '''
        new_integration() raises a ConfigException given an integration configuration with an empty instances property
        given: a factory
        and given: an integration configuration
        and given: a list of receiver creation functions
        and given: a numeric fields set
        when: new_instance() is called
        and when: the integration configuration contains an 'instances' property
            that is the empty list
        then: raise a ConfigException
        '''

        # setup
        config = mod_config.Config({
            'instances': []
        })

        # execute / verify
        with self.assertRaises(ConfigException) as _:
            f = factory.Factory()
            fs = FactoryStub()

            _ = f.new_integration(fs, config, [], set())

    def test_new_integration_raises_config_exception_given_invalid_data_format(self):
        '''
        new_integration() raises a ConfigException given an integration configuration that has an invalid data format value
        and given: an integration configuration
        and given: a list of receiver creation functions
        and given: a numeric fields set
        when: new_instance() is called
        and when: the integration configuration specifies an invalid property
            for newrelic.data_format
        then: raise a ConfigException
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                },
            ],
            'newrelic': {
                'data_format': 'invalid',
            },
        })

        # execute / verify
        with self.assertRaises(ConfigException) as _:
            f = factory.Factory()
            fs = FactoryStub()

            _ = f.new_integration(fs, config, [], set())

    def test_new_integration_raises_config_exception_given_missing_instance_name(self):
        '''
        new_integration() raises a ConfigException given an integration configuration that has an instance without a 'name' property
        and given: an integration configuration
        and given: a list of receiver creation functions
        and given: a numeric fields set
        when: new_instance() is called
        and when: the integration configuration contains an instance without a
            'name' property
        then: raise a ConfigException
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                },
            ],
        })

        # execute / verify
        with self.assertRaises(ConfigException) as _:
            f = factory.Factory()
            fs = FactoryStub()

            _ = f.new_integration(fs, config, [], set())

    def test_new_integration_returns_integration_given_default_data_format_and_single_instance_with_no_labels_or_prefix(self):
        '''
        new_integration() returns an integration instance with the default data format and a single instance with the given instance configuration
        and given: an integration configuration
        and given: a list of receiver creation functions
        and given: a numeric fields set
        when: new_instance() is called
        and when: the integration configuration contains a single valid instance
            configuration
        and when: no data format is specified
        then: return an integration with the default data format and a single
            instance with the given instance configuration
        '''

        # setup
        def new_receiver_func(
            instance_config: mod_config.Config,
            data_cache: cache.DataCache,
            api: mod_api.Api,
        ):
            return ReceiverStub()

        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                    'arguments': {
                        'api_ver': '60.0',
                        'token_url': 'https://my.salesforce.test',
                    }
                },
            ],
        })
        new_relic = NewRelicStub()
        telemetry = TelemetryStub()

        # execute
        f = factory.Factory()
        fs = FactoryStub(
            new_relic=new_relic,
            telemetry=telemetry
        )

        i = f.new_integration(fs, config, [new_receiver_func], set())

        # verify
        self.assertIsNotNone(i)
        self.assertEqual(type(i), integration.Integration)
        self.assertEqual(i.telemetry, telemetry)
        self.assertEqual(len(i.instances), 1)
        instance = i.instances[0]
        self.assertEqual(type(instance), InstanceStub)
        self.assertEqual(instance.name, 'test-inst-1')
        self.assertEqual(instance.instance_config.prefix, '')
        self.assertEqual(
            instance.instance_config.config,
            config['instances'][0]['arguments'],
        )
        self.assertEqual(instance.data_format, DataFormat.LOGS)
        self.assertEqual(instance.new_relic, new_relic)
        self.assertEqual(len(instance.receivers), 1)
        self.assertEqual(instance.receivers[0], new_receiver_func)
        self.assertEqual(instance.labels, { 'nr-labs': 'data' })
        self.assertEqual(instance.numeric_fields_list, set())

    def test_new_integration_returns_integration_given_events_data_format_and_single_instance_with_labels_and_no_prefix(self):
        '''
        new_integration() returns an integration instance with the events data format and a single instance with the given instance configuration
        and given: an integration configuration
        and given: a list of receiver creation functions
        and given: a numeric fields set
        when: new_instance() is called
        and when: the integration configuration contains a single valid instance
            configuration
        and when: the instance configuration contains a labels property
        and when: 'events' is specified as the data format
        then: return an integration with the events data format and a single
            instance with the given instance configuration, including the given
            labels
        '''

        # setup
        def new_receiver_func(
            instance_config: mod_config.Config,
            data_cache: cache.DataCache,
            api: mod_api.Api,
        ):
            return ReceiverStub()

        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                    'arguments': {
                        'api_ver': '60.0',
                        'token_url': 'https://my.salesforce.test',
                    },
                    'labels': {
                        'foo': 'bar',
                    },
                },
            ],
            'newrelic': { 'data_format': 'events' },
        })
        new_relic = NewRelicStub()
        telemetry = TelemetryStub()

        # execute
        f = factory.Factory()
        fs = FactoryStub(
            new_relic=new_relic,
            telemetry=telemetry
        )

        i = f.new_integration(fs, config, [new_receiver_func], set())

        # verify
        self.assertIsNotNone(i)
        self.assertEqual(type(i), integration.Integration)
        self.assertEqual(i.telemetry, telemetry)
        self.assertEqual(len(i.instances), 1)
        instance = i.instances[0]
        self.assertEqual(type(instance), InstanceStub)
        self.assertEqual(instance.name, 'test-inst-1')
        self.assertEqual(instance.instance_config.prefix, '')
        self.assertEqual(
            instance.instance_config.config,
            config['instances'][0]['arguments'],
        )
        self.assertEqual(instance.data_format, DataFormat.EVENTS)
        self.assertEqual(instance.new_relic, new_relic)
        self.assertEqual(len(instance.receivers), 1)
        self.assertEqual(instance.receivers[0], new_receiver_func)
        self.assertEqual(instance.labels, { 'nr-labs': 'data', 'foo': 'bar' })
        self.assertEqual(instance.numeric_fields_list, set())

    def test_new_integration_returns_integration_given_logs_data_format_and_single_instance_with_labels_and_prefix(self):
        '''
        new_integration() returns an integration instance with the logs data format and a single instance with the given instance configuration
        and given: an integration configuration
        and given: a list of receiver creation functions
        and given: a numeric fields set
        when: new_instance() is called
        and when: the integration configuration contains a single valid instance
            configuration
        and when: the instance configuration contains a labels property
        and when: the instance configuration contains a prefix
        and when: 'logs' is specified as the data format
        then: return an integration with the events data format and a single
            instance with the given instance configuration, including the given
            labels and prefix
        '''

        # setup
        def new_receiver_func(
            instance_config: mod_config.Config,
            data_cache: cache.DataCache,
            api: mod_api.Api,
        ):
            return ReceiverStub()

        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                    'arguments': {
                        'api_ver': '60.0',
                        'token_url': 'https://my.salesforce.test',
                        'auth_env_prefix': 'NR_',
                    },
                    'labels': {
                        'foo': 'bar',
                    },
                },
            ],
            'newrelic': { 'data_format': 'logs' },
        })
        new_relic = NewRelicStub()
        telemetry = TelemetryStub()

        # execute
        f = factory.Factory()
        fs = FactoryStub(
            new_relic=new_relic,
            telemetry=telemetry
        )

        i = f.new_integration(fs, config, [new_receiver_func], set())

        # verify
        self.assertIsNotNone(i)
        self.assertEqual(type(i), integration.Integration)
        self.assertEqual(i.telemetry, telemetry)
        self.assertEqual(len(i.instances), 1)
        instance = i.instances[0]
        self.assertEqual(type(instance), InstanceStub)
        self.assertEqual(instance.name, 'test-inst-1')
        self.assertEqual(instance.instance_config.prefix, 'NR_')
        self.assertEqual(
            instance.instance_config.config,
            config['instances'][0]['arguments'],
        )
        self.assertEqual(instance.data_format, DataFormat.LOGS)
        self.assertEqual(instance.new_relic, new_relic)
        self.assertEqual(len(instance.receivers), 1)
        self.assertEqual(instance.receivers[0], new_receiver_func)
        self.assertEqual(instance.labels, { 'nr-labs': 'data', 'foo': 'bar' })
        self.assertEqual(instance.instance_config.prefix, 'NR_')
        self.assertEqual(instance.numeric_fields_list, set())

    def test_new_integration_returns_integration_given_default_data_format_and_single_instance_and_instance_index(self):
        # setup
        def new_receiver_func(
            instance_config: mod_config.Config,
            data_cache: cache.DataCache,
            api: mod_api.Api,
        ):
            return ReceiverStub()

        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                    'arguments': {
                        'api_ver': '60.0',
                        'token_url': 'https://my.salesforce.test',
                    }
                },
            ],
        })
        new_relic = NewRelicStub()
        telemetry = TelemetryStub()

        # execute
        f = factory.Factory()
        fs = FactoryStub(
            new_relic=new_relic,
            telemetry=telemetry
        )

        i = f.new_integration(fs, config, [new_receiver_func], set(), 0)

        # verify
        self.assertIsNotNone(i)
        self.assertEqual(type(i), integration.Integration)
        self.assertEqual(i.telemetry, telemetry)
        self.assertEqual(len(i.instances), 1)
        instance = i.instances[0]
        self.assertEqual(type(instance), InstanceStub)
        self.assertEqual(instance.name, 'test-inst-1')
        self.assertEqual(instance.instance_config.prefix, '')
        self.assertEqual(
            instance.instance_config.config,
            config['instances'][0]['arguments'],
        )
        self.assertEqual(instance.data_format, DataFormat.LOGS)
        self.assertEqual(instance.new_relic, new_relic)
        self.assertEqual(len(instance.receivers), 1)
        self.assertEqual(instance.receivers[0], new_receiver_func)
        self.assertEqual(instance.labels, { 'nr-labs': 'data' })
        self.assertEqual(instance.numeric_fields_list, set())

    def test_new_new_relic_raises_new_relic_api_exception_given_missing_license_key(self):
        '''
        new_new_relic() raises a NewRelicApiException given the New Relic license key is neither specified in the integration configuration nor environment
        given: an integration configuration
        when: new_new_relic() is called
        and when: the 'license_key' property is not specified in the integration
            configuration
        and when: the license_key is not specified in the environment
        then: raise a NewRelicApiException
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                },
            ],
            'newrelic': {
                'data_format': 'logs',
                'api_endpoint': 'US',
            },
        })

        # execute / verify
        with self.assertRaises(NewRelicApiException) as _:
            f = factory.Factory()
            _ = f.new_new_relic(config, DataFormat.LOGS)

    def test_new_new_relic_raises_new_relic_api_exception_given_missing_region(self):
        '''
        new_new_relic() raises a NewRelicApiException given the region is missing in the integration configuration
        given: an integration configuration
        when: new_new_relic() is called
        and when: the 'region' property is not specified in the integration
            configuration
        then: raise a NewRelicApiException
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                },
            ],
            'newrelic': {
                'data_format': 'logs',
                'license_key': '1234567abcdefg',
            },
        })

        # execute / verify
        with self.assertRaises(NewRelicApiException) as _:
            f = factory.Factory()
            _ = f.new_new_relic(config, DataFormat.LOGS)

    def test_new_new_relic_raises_new_relic_api_exception_given_invalid_region(self):
        '''
        new_new_relic() raises a NewRelicApiException given the region is invalid in the integration configuration
        given: an integration configuration
        when: new_new_relic() is called
        and when: the 'region' property in the integration configuration is
            invalid
        then: raise a NewRelicApiException
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                },
            ],
            'newrelic': {
                'data_format': 'logs',
                'api_endpoint': '__',
                'license_key': '1234567abcdefg',
            },
        })

        # execute / verify
        with self.assertRaises(NewRelicApiException) as _:
            f = factory.Factory()
            _ = f.new_new_relic(config, DataFormat.LOGS)

    def test_new_new_relic_raises_new_relic_api_exception_given_missing_account_id(self):
        '''
        new_new_relic() raises a NewRelicApiException given the account ID is neither specified in the integration configuration nor environment
        given: an integration configuration
        when: new_new_relic() is called
        and when: the data format is EVENTS
        and when: the 'account_id' property is not specified in the integration
            configuration
        and when: the account ID is not specified in the environment
        then: raise a NewRelicApiException
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                },
            ],
            'newrelic': {
                'data_format': 'events',
                'api_endpoint': 'US',
                'license_key': 'abcdefg1234567',
            },
        })

        # execute / verify
        with self.assertRaises(NewRelicApiException) as _:
            f = factory.Factory()
            _ = f.new_new_relic(config, DataFormat.EVENTS)

    def test_new_new_relic_returns_new_relic_instance_with_US_logs_endpoint_given_logs_US_and_license_key(self):
        '''
        new_new_relic() returns a New Relic instance with US Logs API endpoint given the LOGS data format, the US region, and a license key
        given: an integration configuration
        when: new_new_relic() is called
        and when: the data format is LOGS
        and when: the 'region' property in the integration configuration is set
            to US
        and when: a license key is specified
        then: return a New Relic instance with US Logs API endpoint
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                },
            ],
            'newrelic': {
                'data_format': 'logs',
                'api_endpoint': 'US',
                'license_key': 'asdfghjkl',
            },
        })

        # execute
        f = factory.Factory()
        new_relic = f.new_new_relic(config, DataFormat.LOGS)

        # verify
        self.assertIsNotNone(new_relic)
        self.assertEqual(type(new_relic), newrelic.NewRelic)
        self.assertEqual(new_relic.license_key, 'asdfghjkl')
        self.assertEqual(
            new_relic.logs_api_endpoint,
            newrelic.US_LOGGING_ENDPOINT,
        )
        self.assertEqual(
            new_relic.events_api_endpoint,
            None,
        )

    def test_new_new_relic_returns_new_relic_instance_with_EU_logs_endpoint_given_logs_EU_and_license_key(self):
        '''
        new_new_relic() returns a New Relic instance with EU Logs API endpoint given the LOGS data format, the EU region, and a license key
        given: an integration configuration
        when: new_new_relic() is called
        and when: the data format is LOGS
        and when: the 'region' property in the integration configuration is set
            to EU
        and when: a license key is specified
        then: return a New Relic instance with EU Logs API endpoint
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                },
            ],
            'newrelic': {
                'data_format': 'logs',
                'api_endpoint': 'EU',
                'license_key': 'lkjhgfdsa',
            },
        })

        # execute
        f = factory.Factory()
        new_relic = f.new_new_relic(config, DataFormat.LOGS)

        # verify
        self.assertIsNotNone(new_relic)
        self.assertEqual(type(new_relic), newrelic.NewRelic)
        self.assertEqual(new_relic.license_key, 'lkjhgfdsa')
        self.assertEqual(
            new_relic.logs_api_endpoint,
            newrelic.EU_LOGGING_ENDPOINT,
        )
        self.assertEqual(
            new_relic.events_api_endpoint,
            None,
        )

    def test_new_new_relic_returns_new_relic_instance_with_US_events_endpoint_given_events_US_account_id_and_license_key(self):
        '''
        new_new_relic() returns a New Relic instance with US Events API endpoint given the EVENTS data format, the US region, an account ID, and a license key
        given: an integration configuration
        when: new_new_relic() is called
        and when: the data format is EVENTS
        and when: the 'account_id' property is set in the integration
            configuration
        and when: the 'region' property in the integration configuration is set
            to US
        and when: a license key is specified
        then: return a New Relic instance with US Events API endpoint
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                },
            ],
            'newrelic': {
                'data_format': 'events',
                'api_endpoint': 'US',
                'account_id': 123456,
                'license_key': '1234567890',
            },
        })

        # execute
        f = factory.Factory()
        new_relic = f.new_new_relic(config, DataFormat.EVENTS)

        # verify
        self.assertIsNotNone(new_relic)
        self.assertEqual(type(new_relic), newrelic.NewRelic)
        self.assertEqual(new_relic.license_key, '1234567890')
        self.assertEqual(
            new_relic.logs_api_endpoint,
            None,
        )
        self.assertEqual(
            new_relic.events_api_endpoint,
            newrelic.US_EVENTS_ENDPOINT.format(
                account_id=123456,
            ),
        )

    def test_new_new_relic_returns_new_relic_instance_with_EU_events_endpoint_given_events_EU_account_id_and_license_key(self):
        '''
        new_new_relic() returns a New Relic instance with EU Events API endpoint given the EVENTS data format, the EU region, an account ID, and a license key
        given: an integration configuration
        when: new_new_relic() is called
        and when: the 'account_id' property is set in the integration
            configuration
        and when: the 'region' property in the integration configuration is set
            to EU
        and when: a license key is specified
        then: return a New Relic instance with EU Events API endpoint
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                },
            ],
            'newrelic': {
                'data_format': 'events',
                'api_endpoint': 'EU',
                'account_id': 567890,
                'license_key': '9876543210',
            },
        })

        # execute
        f = factory.Factory()
        new_relic = f.new_new_relic(config, DataFormat.EVENTS)

        # verify
        self.assertIsNotNone(new_relic)
        self.assertEqual(type(new_relic), newrelic.NewRelic)
        self.assertEqual(new_relic.license_key, '9876543210')
        self.assertEqual(
            new_relic.logs_api_endpoint,
            None,
        )
        self.assertEqual(
            new_relic.events_api_endpoint,
            newrelic.EU_EVENTS_ENDPOINT.format(
                account_id=567890,
            ),
        )

    def test_new_telemetry_returns_telemetry_instance_with_default_integration_name_given_no_name_in_config(self):
        '''
        new_telemetry() returns a Telemetry instance with the default integration name when no name is given in the integration configuration
        given: an integration configuration
        and given: a NewRelic instance
        when: new_telemetry() is called
        and when: the 'integration_name' property is not set in the integration configuraiton
        then: return a Telemetry instance with the default integration name
        '''

        # setup
        config = mod_config.Config({})
        new_relic = NewRelicStub()

        # execute
        f = factory.Factory()
        telemetry = f.new_telemetry(config, new_relic)

        # verify
        self.assertIsNotNone(telemetry)
        self.assertEqual(type(telemetry), mod_telemetry.Telemetry)
        self.assertEqual(
            telemetry.integration_name,
            'com.newrelic.labs.salesforce.exporter',
        )

    def test_new_telemetry_returns_telemetry_instance_with_given_integration_name_in_config(self):
        '''
        new_telemetry() returns a Telemetry instance with the integration name given in the integration configuration
        given: an integration configuration
        and given: a NewRelic instance
        when: new_telemetry() is called
        and when: the 'integration_name' property is set in the integration configuraiton
        then: return a Telemetry instance with the given integration name
        '''

        # setup
        config = mod_config.Config({
            'integration_name': 'foo.bar.beep.boop',
        })
        new_relic = NewRelicStub()

        # execute
        f = factory.Factory()
        telemetry = f.new_telemetry(config, new_relic)

        # verify
        self.assertIsNotNone(telemetry)
        self.assertEqual(type(telemetry), mod_telemetry.Telemetry)
        self.assertEqual(
            telemetry.integration_name,
            'foo.bar.beep.boop',
        )
