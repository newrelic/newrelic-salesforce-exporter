import unittest

from . import \
    BackendStub, \
    BackendFactoryStub
from newrelic_logging import \
    config as mod_config, \
    cache, \
    factory

class TestFactory(unittest.TestCase):
    def test_new_data_cache_returns_none_if_disabled(self):
        '''
        new_data_cache() returns None if cache disabled
        given: a backend factory and a configuration
        when: new_data_cache() is called
        and when: cache_enabled is False in config
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
        given: a backend factory and a configuration
        when: new_data_cache() is called
        and when: cache_enabled is True in config
        then: a DataCache is returned with the a backend from the specified backend factory
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

    def test_new_data_cache_raises_if_backend_factory_does(self):
        '''
        new_data_cache() raises CacheException if backend factory does
        given: a backend factory and a configuration
        when: new_data_cache() is called
        and when: backend factory new_data_cache() raises any exception
        then: a CacheException is raised
        '''

        # setup
        instance_config = mod_config.Config({ 'cache_enabled': 'true' })
        backend_factory = BackendFactoryStub(raise_error=True)

        # execute / verify
        f = factory.Factory()

        with self.assertRaises(cache.CacheException):
            _ = f.new_data_cache(instance_config, backend_factory)

    def test_new_authenticator(self):
        pass

    def test_new_api(self):
        pass

    def test_new_pipeline(self):
        pass

    def test_new_instance(self):
        pass
