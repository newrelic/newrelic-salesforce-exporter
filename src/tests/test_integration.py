import unittest

from . import ApiFactoryStub, \
    AuthenticatorFactoryStub, \
    CacheFactoryStub, \
    NewRelicStub, \
    NewRelicFactoryStub, \
    PipelineFactoryStub, \
    QueryFactoryStub, \
    SalesForceFactoryStub
from newrelic_logging import ConfigException, \
    DataFormat, \
    config as mod_config, \
    integration

class TestIntegration(unittest.TestCase):
    def test_build_instance(self):
        '''
        given: a Config instance, a NewRelic instance, a data format, a set of
               event type field mappings, a set of numeric fields an initial
               delay, an instance config, and a instance index
        when: no prefix or queries are provided in the instance config
        then: return a Salesforce instance configured with appropriate values
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                    'labels': {
                        'foo': 'bar',
                        'beep': 'boop',
                    },
                    'arguments': {
                        'token_url': 'https://my.salesforce.test/token',
                        'cache_enabled': False,
                    },
                }
            ]
        })
        api_factory = ApiFactoryStub()
        auth_factory = AuthenticatorFactoryStub()
        cache_factory = CacheFactoryStub()
        pipeline_factory = PipelineFactoryStub()
        salesforce_factory = SalesForceFactoryStub()
        query_factory = QueryFactoryStub()
        new_relic = NewRelicStub(config)
        event_type_fields_mapping = { 'event': ['field1'] }
        numeric_fields_list = set(['field1', 'field2'])

        # execute
        instance = integration.build_instance(
            config,
            auth_factory,
            cache_factory,
            pipeline_factory,
            salesforce_factory,
            api_factory,
            query_factory,
            new_relic,
            DataFormat.EVENTS,
            event_type_fields_mapping,
            numeric_fields_list,
            603,
            config['instances'][0],
            0,
        )

        # verify
        self.assertTrue('client' in instance)
        self.assertTrue('name' in instance)
        self.assertEqual(instance['name'], 'test-inst-1')
        client = instance['client']
        self.assertEqual(client.instance_name, 'test-inst-1')
        inst_config = client.config
        self.assertIsNotNone(inst_config)
        self.assertEqual(inst_config.prefix, '')
        self.assertTrue('token_url' in inst_config)
        data_cache = client.data_cache
        self.assertIsNotNone(data_cache)
        self.assertIsNotNone(data_cache.config)
        self.assertTrue('cache_enabled' in data_cache.config)
        self.assertFalse(data_cache.config['cache_enabled'])
        authenticator = client.authenticator
        self.assertIsNotNone(authenticator)
        self.assertEqual(authenticator.data_cache, data_cache)
        self.assertIsNotNone(authenticator.config)
        self.assertEqual(
            authenticator.config['token_url'],
            'https://my.salesforce.test/token',
        )
        p = client.pipeline
        self.assertIsNotNone(p)
        self.assertEqual(p.data_cache, data_cache)
        self.assertEqual(p.new_relic, new_relic)
        self.assertEqual(p.data_format, DataFormat.EVENTS)
        self.assertIsNotNone(p.labels)
        self.assertTrue(type(p.labels) is dict)
        labels = p.labels
        self.assertTrue('foo' in labels)
        self.assertEqual(labels['foo'], 'bar')
        self.assertTrue('beep' in labels)
        self.assertEqual(labels['beep'], 'boop')
        self.assertIsNotNone(p.event_type_fields_mapping)
        self.assertTrue(type(p.event_type_fields_mapping) is dict)
        event_type_fields_mapping = p.event_type_fields_mapping
        self.assertTrue('event' in event_type_fields_mapping)
        self.assertTrue(type(event_type_fields_mapping['event']) is list)
        self.assertEqual(len(event_type_fields_mapping['event']), 1)
        self.assertEqual(event_type_fields_mapping['event'][0], 'field1')
        self.assertIsNotNone(p.numeric_fields_list)
        self.assertTrue(type(p.numeric_fields_list) is set)
        numeric_fields_list = p.numeric_fields_list
        self.assertEqual(len(numeric_fields_list), 2)
        self.assertTrue('field1' in numeric_fields_list)
        self.assertTrue('field2' in numeric_fields_list)
        self.assertEqual(client.query_factory, query_factory)
        self.assertEqual(client.initial_delay, 603)
        self.assertIsNone(client.queries)

        '''
        given: a Config instance, a NewRelic instance, a data format, a set of
               event type field mappings, a set of numeric fields an initial
               delay, an instance config, and a instance index
        when: prefix provided in the instance config
        then: the prefix should be set on the instance config object
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                    'labels': {
                        'foo': 'bar',
                        'beep': 'boop',
                    },
                    'arguments': {
                        'token_url': 'https://my.salesforce.test/token',
                        'cache_enabled': False,
                        'auth_env_prefix': 'ABCDEF_'
                    },
                }
            ]
        })
        api_factory = ApiFactoryStub()
        auth_factory = AuthenticatorFactoryStub()
        cache_factory = CacheFactoryStub()
        pipeline_factory = PipelineFactoryStub()
        salesforce_factory = SalesForceFactoryStub()
        query_factory = QueryFactoryStub()

        # execute
        instance = integration.build_instance(
            config,
            auth_factory,
            cache_factory,
            pipeline_factory,
            salesforce_factory,
            api_factory,
            query_factory,
            new_relic,
            DataFormat.EVENTS,
            event_type_fields_mapping,
            numeric_fields_list,
            603,
            config['instances'][0],
            0,
        )

        # verify
        self.assertTrue('client' in instance)
        client = instance['client']
        inst_config = client.config
        self.assertIsNotNone(inst_config)
        self.assertEqual(inst_config.prefix, 'ABCDEF_')

        '''
        given: a Config instance, a NewRelic instance, a data format, a set of
               event type field mappings, a set of numeric fields an initial
               delay, an instance config, and a instance index
        when: queries provide in the config
        then: queries should be set in the Salesforce client instance
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                    'labels': {
                        'foo': 'bar',
                        'beep': 'boop',
                    },
                    'arguments': {
                        'token_url': 'https://my.salesforce.test/token',
                        'cache_enabled': False,
                    },
                }
            ],
            'queries': [
                {
                    'query': 'SELECT foo FROM Account'
                }
            ]
        })
        api_factory = ApiFactoryStub()
        auth_factory = AuthenticatorFactoryStub()
        cache_factory = CacheFactoryStub()
        pipeline_factory = PipelineFactoryStub()
        salesforce_factory = SalesForceFactoryStub()
        query_factory = QueryFactoryStub()

        # execute
        instance = integration.build_instance(
            config,
            auth_factory,
            cache_factory,
            pipeline_factory,
            salesforce_factory,
            api_factory,
            query_factory,
            new_relic,
            DataFormat.EVENTS,
            event_type_fields_mapping,
            numeric_fields_list,
            603,
            config['instances'][0],
            0,
        )

        # verify
        self.assertTrue('client' in instance)
        client = instance['client']
        self.assertIsNotNone(client.queries)
        self.assertEqual(len(client.queries), 1)
        self.assertTrue('query' in client.queries[0])
        self.assertEqual(client.queries[0]['query'], 'SELECT foo FROM Account')

    def test_init(self):
        '''
        given: a Config instance, set of factories, a data format, an event
               type fields mapping, a set of numeric fields and an initial
               delay
        when: an integration instance is created
        then: instances should be created with pipelines that use the correct
              data format and a newrelic instance should be created with the
              correct config instance
        '''

        # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                    'labels': {
                        'foo': 'bar',
                        'beep': 'boop',
                    },
                    'arguments': {
                        'token_url': 'https://my.salesforce.test/token',
                        'cache_enabled': False,
                    },
                },
                {
                    'name': 'test-inst-2',
                    'labels': {
                        'foo': 'bar',
                        'beep': 'boop',
                    },
                    'arguments': {
                        'token_url': 'https://my.salesforce.test/token',
                        'cache_enabled': False,
                    },
                }
            ],
            'newrelic': {
                'data_format': 'events',
            }
        })

        api_factory = ApiFactoryStub()
        auth_factory = AuthenticatorFactoryStub()
        cache_factory = CacheFactoryStub()
        pipeline_factory = PipelineFactoryStub()
        salesforce_factory = SalesForceFactoryStub()
        query_factory = QueryFactoryStub()
        newrelic_factory = NewRelicFactoryStub()
        event_type_fields_mapping = { 'event': ['field1'] }
        numeric_fields_list = set(['field1', 'field2'])

        # execute

        i = integration.Integration(
            config,
            auth_factory,
            cache_factory,
            pipeline_factory,
            salesforce_factory,
            api_factory,
            query_factory,
            newrelic_factory,
            event_type_fields_mapping,
            numeric_fields_list,
            603
        )

        # verify

        self.assertIsNotNone(i.instances)
        self.assertTrue(type(i.instances) is list)
        self.assertEqual(len(i.instances), 2)
        self.assertTrue('client' in i.instances[0])
        self.assertTrue('name' in i.instances[0])
        self.assertEqual(i.instances[0]['name'], 'test-inst-1')
        self.assertTrue('client' in i.instances[1])
        self.assertTrue('name' in i.instances[1])
        self.assertEqual(i.instances[1]['name'], 'test-inst-2')
        client = i.instances[0]['client']
        self.assertEqual(client.pipeline.data_format, DataFormat.EVENTS)
        client = i.instances[1]['client']
        self.assertEqual(client.pipeline.data_format, DataFormat.EVENTS)
        self.assertIsNotNone(i.new_relic)
        self.assertIsNotNone(i.new_relic.config)
        self.assertEqual(i.new_relic.config, config)

        '''
        given: a Config instance, set of factories, a data format, an event
               type fields mapping, a set of numeric fields and an initial
               delay
        when: an integration instance is created
        then: an exception should be raised if an invalid data format is
              passed
        '''

                # setup
        config = mod_config.Config({
            'instances': [
                {
                    'name': 'test-inst-1',
                    'labels': {
                        'foo': 'bar',
                        'beep': 'boop',
                    },
                    'arguments': {
                        'token_url': 'https://my.salesforce.test/token',
                        'cache_enabled': False,
                    },
                },
            ],
            'newrelic': {
                'data_format': 'invalid',
            }
        })

        api_factory = ApiFactoryStub()
        auth_factory = AuthenticatorFactoryStub()
        cache_factory = CacheFactoryStub()
        pipeline_factory = PipelineFactoryStub()
        salesforce_factory = SalesForceFactoryStub()
        query_factory = QueryFactoryStub()
        newrelic_factory = NewRelicFactoryStub()

        # execute/verify

        with self.assertRaises(ConfigException):
            i = integration.Integration(
                config,
                auth_factory,
                cache_factory,
                pipeline_factory,
                salesforce_factory,
                api_factory,
                query_factory,
                newrelic_factory,
                event_type_fields_mapping,
                numeric_fields_list,
                603
            )

        '''
        given: a Config instance, set of factories, a data format, an event
               type fields mapping, a set of numeric fields and an initial
               delay
        when: no instance configurations are provided
        then: integration instances should be the empty set
        '''

                # setup
        config = mod_config.Config({
            'instances': [],
            'newrelic': {
                'data_format': 'logs',
            }
        })

        api_factory = ApiFactoryStub()
        auth_factory = AuthenticatorFactoryStub()
        cache_factory = CacheFactoryStub()
        pipeline_factory = PipelineFactoryStub()
        salesforce_factory = SalesForceFactoryStub()
        query_factory = QueryFactoryStub()
        newrelic_factory = NewRelicFactoryStub()

        # execute

        i = integration.Integration(
            config,
            auth_factory,
            cache_factory,
            pipeline_factory,
            salesforce_factory,
            api_factory,
            query_factory,
            newrelic_factory,
            event_type_fields_mapping,
            numeric_fields_list,
            603
        )

        # verify

        self.assertEqual(len(i.instances), 0)

        '''
        given: a Config instance, set of factories, a data format, an event
               type fields mapping, a set of numeric fields and an initial
               delay
        when: instances property is missing
        then: integration instances should be the empty set
        '''

        # setup
        config = mod_config.Config({
            'newrelic': {
                'data_format': 'logs',
            }
        })

        api_factory = ApiFactoryStub()
        auth_factory = AuthenticatorFactoryStub()
        cache_factory = CacheFactoryStub()
        pipeline_factory = PipelineFactoryStub()
        salesforce_factory = SalesForceFactoryStub()
        query_factory = QueryFactoryStub()
        newrelic_factory = NewRelicFactoryStub()

        # execute

        i = integration.Integration(
            config,
            auth_factory,
            cache_factory,
            pipeline_factory,
            salesforce_factory,
            api_factory,
            query_factory,
            newrelic_factory,
            event_type_fields_mapping,
            numeric_fields_list,
            603
        )

        # verify

        self.assertEqual(len(i.instances), 0)
