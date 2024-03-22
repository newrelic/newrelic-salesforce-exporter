from datetime import timedelta
from redis import RedisError
import unittest

from newrelic_logging import cache, CacheException, config as mod_config
from . import RedisStub, BackendStub, BackendFactoryStub

class TestRedisBackend(unittest.TestCase):
    def test_exists(self):
        '''
        backend exists returns redis exists
        given: a redis instance
        when: exists is called
        then: the redis instance exists command result is returned
        '''

        # setup
        redis = RedisStub({ 'foo': 'bar', 'beep': 'boop' })

        # execute
        backend = cache.RedisBackend(redis)
        foo_exists = backend.exists('foo')
        baz_exists = backend.exists('baz')

        # verify
        self.assertTrue(foo_exists)
        self.assertFalse(baz_exists)

    def test_exists_raises_when_redis_does(self):
        '''
        backend exists raises error if redis exists does
        given: a redis instance
        when: exists is called
        and when: the redis instance raises an exception
        then: the redis instance exception is raised
        '''

        # setup
        redis = RedisStub({ 'foo': 'bar', 'beep': 'boop' }, raise_error=True)

        # execute
        backend = cache.RedisBackend(redis)

        # verify
        with self.assertRaises(RedisError):
            backend.exists('foo')

    def test_put(self):
        '''
        backend put calls redis set
        given: a redis instance
        when: put is called
        then: the redis instance set command is called
        '''

        # setup
        redis = RedisStub({ 'foo': 'bar', 'beep': 'boop' })

        # preconditions
        self.assertFalse(redis.exists('r2'))

        # execute
        backend = cache.RedisBackend(redis)
        backend.put('r2', 'd2')

        # verify
        self.assertTrue(redis.exists('r2'))
        self.assertEqual(redis.test_cache['r2'], 'd2')

    def test_put_raises_if_redis_does(self):
        '''
        backend put raises error if redis set does
        given: a redis instance
        when: put is called
        and when: the redis instance raises an exception
        then: the redis instance exception is raised
        '''

        # setup
        redis = RedisStub({ 'foo': 'bar', 'beep': 'boop' }, raise_error=True)

        # execute
        backend = cache.RedisBackend(redis)

        # verify
        with self.assertRaises(RedisError) as _:
            backend.put('r2', 'd2')


    def test_get_set(self):
        '''
        backend calls redis smembers
        given: a redis instance
        when: get_set is called
        and when: key does not exist
        or when: key exists and is set
        then: the redis instance smembers command result is returned
        '''

        # setup
        redis = RedisStub({ 'foo': set(['bar']) })

        # execute
        backend = cache.RedisBackend(redis)
        foo_set = backend.get_set('foo')
        beep_set = backend.get_set('beep')

        # verify
        self.assertEqual(len(foo_set), 1)
        self.assertEqual(foo_set, set(['bar']))
        self.assertEqual(len(beep_set), 0)
        self.assertEqual(beep_set, set())

    def test_get_set_raises_if_redis_does(self):
        '''
        backend raises exception if redis smembers does
        given: a redis instance
        when: get_set is called
        and when: redis instance raises an exception
        then: the redis instance exception is raised
        '''

        # setup
        redis = RedisStub({ 'foo': 'bar' })

        # execute
        backend = cache.RedisBackend(redis)

        # verify
        with self.assertRaises(RedisError) as _:
            backend.get_set('foo')

    def test_set_add(self):
        '''
        backend set_add calls sadd
        given: a redis instance
        when: set_add is called
        and when: key does not exist
        or when: key exists and is set
        then: the redis instance sadd command is called
        '''

        # setup
        redis = RedisStub({ 'foo': set(['bar', 'beep', 'boop']) })

        # execute
        backend = cache.RedisBackend(redis)
        backend.set_add('foo', 'baz')
        backend.set_add('bop', 'biz')

        args = [1, 2, 3]
        backend.set_add('bip', *args)

        # verify
        self.assertEqual(
            redis.test_cache['foo'], set(['bar', 'beep', 'boop', 'baz']),
        )
        self.assertEqual(redis.test_cache['bop'], set(['biz']))
        self.assertEqual(redis.test_cache['bip'], set([1, 2, 3]))

    def test_set_add_raises_if_redis_does(self):
        '''
        backend raises exception if redis sadd does
        given: a redis instance
        when: set_add is called
        and when: redis instance raises an exception
        then: the redis instance exception is raised
        '''

        # setup
        redis = RedisStub({ 'foo': 'bar' })

        # execute
        backend = cache.RedisBackend(redis)

        # verify
        with self.assertRaises(RedisError) as _:
            backend.set_add('foo', 'beep')

    def test_set_expiry(self):
        '''
        backend set_expiry calls expire
        given: a redis instance
        when: set_expiry is called
        then: the redis instance expire command is called
        '''

        # setup
        redis = RedisStub({ 'foo': set('bar') })

        # execute
        backend = cache.RedisBackend(redis)
        backend.set_expiry('foo', 5)

        # verify
        self.assertTrue('foo' in redis.expiry)
        self.assertEqual(redis.expiry['foo'], timedelta(5))

    def test_set_expiry_raises_if_redis_does(self):
        '''
        backend set_expiry raises exception if redis expire does
        given: a redis instance
        when: set_expiry is called
        and when: redis instance raises an exception
        then: the redis instance exception is raised
        '''

        # setup
        redis = RedisStub({ 'foo': set('bar') }, raise_error=True)

        # execute
        backend = cache.RedisBackend(redis)

        # verify
        with self.assertRaises(RedisError) as _:
            backend.set_expiry('foo', 5)


class TestBufferedAddSetCache(unittest.TestCase):
    def test_check_or_set_true_when_item_exists(self):
        '''
        check_or_set returns true when item exists
        given: a set
        and when: the set contains the item to be checked
        then: returns true
        '''

        # execute
        s = cache.BufferedAddSetCache(set(['foo']))
        contains_foo = s.check_or_set('foo')

        # verify
        self.assertTrue(contains_foo)

    def test_check_or_set_false_and_adds_item_when_item_missing(self):
        '''
        check_or_set returns false and adds item when item is not in set
        given: a set
        when: the set does not contain the item to be checked
        then: returns false
        and then: the item is in the set
        '''

        # execute
        s = cache.BufferedAddSetCache(set())
        contains_foo = s.check_or_set('foo')

        # verify
        self.assertFalse(contains_foo)
        self.assertTrue('foo' in s.get_buffer())

    def test_check_or_set_checks_both_sets(self):
        '''
        check_or_set checks both the given set and buffer for each check_or_set
        given: a set
        when: the set does not contain the item to be checked
        then: returns false
        and then: the item is in the set
        and when: the item is added again
        then: returns true
        '''

        # execute
        s = cache.BufferedAddSetCache(set())
        contains_foo = s.check_or_set('foo')

        # verify
        self.assertFalse(contains_foo)
        self.assertTrue('foo' in s.get_buffer())

        # execute
        contains_foo = s.check_or_set('foo')

        # verify
        # this verifies that check_or_set also checks the buffer
        self.assertTrue(contains_foo)


class TestDataCache(unittest.TestCase):
    def test_can_skip_download_logfile_true_when_key_exists(self):
        '''
        dl logfile returns true if key exists in cache
        given: a backend instance
        when: can_skip_download_logfile is called
        and when: the key exists in the cache
        then: return true
        '''

        # setup
        backend = BackendStub({ 'foo': ['bar'] })

        # execute
        data_cache = cache.DataCache(backend, 5)
        can = data_cache.can_skip_downloading_logfile('foo')

        # verify
        self.assertTrue(can)

    def test_can_skip_download_logfile_false_when_key_missing(self):
        '''
        dl logfile returns false if key does not exist
        given: a backend instance
        when: can_skip_download_logfile is called
        and when: the key does not exist in the backend
        then: return false
        '''

        # setup
        backend = BackendStub({})

        # execute
        data_cache = cache.DataCache(backend, 5)
        can = data_cache.can_skip_downloading_logfile('foo')

        # verify
        self.assertFalse(can)

    def test_can_skip_download_logfile_raises_if_backend_does(self):
        '''
        dl logfile raises CacheException if backend raises any Exception
        given: a backend instance
        when: can_skip_download_logfile is called
        and when: backend raises any exception
        then: a CacheException is raised
        '''

        # setup
        backend = BackendStub({}, raise_error=True)

        # execute
        data_cache = cache.DataCache(backend, 5)

        # verify
        with self.assertRaises(CacheException) as _:
            data_cache.can_skip_downloading_logfile('foo')

    def test_check_or_set_log_line_true_when_exists(self):
        '''
        check_or_set_log_line returns true when line ID is in the cached set
        given: a backend instance
        when: check_or_set_log_line is called
        and when: row['REQUEST_ID'] is in the set for key
        then: returns true
        '''

        # setup
        backend = BackendStub({ 'foo': set(['bar']) })
        line = { 'REQUEST_ID': 'bar' }

        # execute
        data_cache = cache.DataCache(backend, 5)
        val = data_cache.check_or_set_log_line('foo', line)

        # verify
        self.assertTrue(val)

    def test_check_or_set_log_line_false_and_adds_when_missing(self):
        '''
        check_or_set_log_line returns false and adds line ID when line ID is not in the cached set
        given: a backend instance
        when: check_or_set_log_line is called
        and when: row['REQUEST_ID'] is not in set for key
        then: the line ID is added to the set and false is returned
        '''

        # setup
        backend = BackendStub({ 'foo': set() })
        row = { 'REQUEST_ID': 'bar' }

        # preconditions
        self.assertFalse('bar' in backend.redis.test_cache['foo'])

        # execute
        data_cache = cache.DataCache(backend, 5)
        val = data_cache.check_or_set_log_line('foo', row)

        # verify
        self.assertFalse(val)

        # Need to flush before we can check the cache as how it is stored
        # in memory is an implementation detail
        data_cache.flush()
        self.assertTrue('bar' in backend.redis.test_cache['foo'])

    def test_check_or_set_log_line_raises_if_backend_does(self):
        '''
        check_or_set_log_line raises CacheException if backend raises any Exception
        given: a backend instance
        when: check_or_set_log_line is called
        and when: backend raises any exception
        then: a CacheException is raised
        '''

        # setup
        backend = BackendStub({}, raise_error=True)
        line = { 'REQUEST_ID': 'bar' }

        # execute / verify
        data_cache = cache.DataCache(backend, 5)

        with self.assertRaises(CacheException) as _:
            data_cache.check_or_set_log_line('foo', line)

    def test_check_or_set_event_id_true_when_exists(self):
        '''
        check_or_set_event_id returns true when event ID is in the cached set
        given: a backend instance
        when: check_or_set_event_id is called
        and when: event ID is in the set 'event_ids'
        then: returns true
        '''

        # setup
        backend = BackendStub({ 'event_ids': set(['foo']) })

        # execute
        data_cache = cache.DataCache(backend, 5)
        val = data_cache.check_or_set_event_id('foo')

        # verify
        self.assertTrue(val)

    def test_check_or_set_event_id_false_and_adds_when_missing(self):
        '''
        check_or_set_event_id returns false and adds event ID when event ID is not in the cached set
        given: a backend instance
        when: check_or_set_event_id is called
        and when: event ID is not in set 'event_ids'
        then: the event ID is added to the set and False is returned
        '''

        # setup
        backend = BackendStub({ 'event_ids': set() })

        # preconditions
        self.assertFalse('foo' in backend.redis.test_cache['event_ids'])

        # execute
        data_cache = cache.DataCache(backend, 5)
        val = data_cache.check_or_set_event_id('foo')

        # verify
        self.assertFalse(val)

        # Need to flush before we can check the cache as how it is stored
        # in memory is an implementation detail
        data_cache.flush()
        self.assertTrue('foo' in backend.redis.test_cache['event_ids'])

    def test_check_or_set_event_id_raises_if_backend_does(self):
        '''
        check_or_set_event_id raises CacheException if backend raises any Exception
        given: a backend instance
        when: check_or_set_event_id is called
        and when: backend raises any exception
        then: a CacheException is raised
        '''

        # setup
        backend = BackendStub({}, raise_error=True)

        # execute / verify
        data_cache = cache.DataCache(backend, 5)

        with self.assertRaises(CacheException) as _:
            data_cache.check_or_set_event_id('foo')

    def test_flush_does_not_affect_cache_when_add_buffers_empty(self):
        '''
        backend cache is empty if flush is called when BufferedAddSet buffers are empty
        given: a backend instance
        when: flush is called
        and when: the log lines and event ID add buffers are empty
        then: the backend cache remains empty
        '''

        # setup
        backend = BackendStub({})

        # preconditions
        self.assertEqual(len(backend.redis.test_cache), 0)

        # execute
        data_cache = cache.DataCache(backend, 5)
        data_cache.flush()

        # verify
        self.assertEqual(len(backend.redis.test_cache), 0)

    def test_flush_writes_log_lines_when_add_buffer_not_empty(self):
        '''
        flush writes any buffered log lines when log lines add buffer is not empty
        given: a backend instance
        when: flush is called
        and when: the log lines add buffer is not empty
        then: the backend cache is updated with items from the add buffer
        '''

        # setup
        backend = BackendStub({})
        line1 = { 'REQUEST_ID': 'bar1' }
        line2 = { 'REQUEST_ID': 'bar2' }
        line3 = { 'REQUEST_ID': 'boop' }

        # preconditions
        self.assertEqual(len(backend.redis.test_cache), 0)

        # execute
        data_cache = cache.DataCache(backend, 5)
        data_cache.check_or_set_log_line('foo', line1)
        data_cache.check_or_set_log_line('foo', line2)
        data_cache.check_or_set_log_line('beep', line3)
        data_cache.flush()

        # verify
        self.assertEqual(len(backend.redis.test_cache), 2)
        self.assertTrue('foo' in backend.redis.test_cache)
        self.assertEqual(backend.redis.test_cache['foo'], set(['bar1', 'bar2']))
        self.assertTrue('beep' in backend.redis.test_cache)
        self.assertEqual(backend.redis.test_cache['beep'], set(['boop']))

    def test_flush_writes_event_ids_when_add_buffer_not_empty(self):
        '''
        flush writes any buffered event IDs when event IDs add buffer is not empty
        given: a backend instance
        when: flush is called
        and when: the event IDs add buffer is not empty
        then: the backend cache is updated with items from the add buffer
        '''

        # setup
        backend = BackendStub({})

        # preconditions
        self.assertEqual(len(backend.redis.test_cache), 0)

        # execute
        data_cache = cache.DataCache(backend, 5)
        data_cache.check_or_set_event_id('foo')
        data_cache.check_or_set_event_id('bar')
        data_cache.check_or_set_event_id('beep')
        data_cache.check_or_set_event_id('boop')
        data_cache.flush()

        # verify
        self.assertEqual(len(backend.redis.test_cache), 5)
        self.assertTrue('event_ids' in backend.redis.test_cache)
        self.assertEqual(
            backend.redis.test_cache['event_ids'],
            set(['foo', 'bar', 'beep', 'boop'])
        )
        self.assertTrue('foo' in backend.redis.test_cache)
        self.assertEqual(backend.redis.test_cache['foo'], 1)
        self.assertTrue('bar' in backend.redis.test_cache)
        self.assertEqual(backend.redis.test_cache['bar'], 1)
        self.assertTrue('beep' in backend.redis.test_cache)
        self.assertEqual(backend.redis.test_cache['beep'], 1)
        self.assertTrue('boop' in backend.redis.test_cache)
        self.assertEqual(backend.redis.test_cache['boop'], 1)

    def test_flush_sets_expiry_on_write(self):
        '''
        flush sets the expiry time of any keys it writes
        given: a backend instance and expiry
        when: flush is called
        and when: add buffers are not empty
        then: the backend cache is updated with new cached sets with specified expiration time
        '''

        # setup
        backend = BackendStub({})
        line1 = { 'REQUEST_ID': 'bar' }

        # preconditions
        self.assertEqual(len(backend.redis.test_cache), 0)
        self.assertEqual(len(backend.redis.expiry), 0)

        # execute
        data_cache = cache.DataCache(backend, 5)
        data_cache.check_or_set_log_line('foo', line1)
        data_cache.check_or_set_event_id('bar')
        data_cache.flush()

        # verify
        self.assertEqual(len(backend.redis.test_cache), 3)
        self.assertTrue('foo' in backend.redis.test_cache)
        self.assertEqual(backend.redis.test_cache['foo'], set(['bar']))
        self.assertTrue('event_ids' in backend.redis.test_cache)
        self.assertEqual(backend.redis.test_cache['event_ids'], set(['bar']))
        self.assertTrue('bar' in backend.redis.test_cache)
        self.assertEqual(backend.redis.test_cache['bar'], 1)
        self.assertEqual(len(backend.redis.expiry), 3)
        self.assertTrue('foo' in backend.redis.expiry)
        self.assertEqual(backend.redis.expiry['foo'], timedelta(days=5))
        self.assertTrue('bar' in backend.redis.expiry)
        self.assertEqual(backend.redis.expiry['bar'], timedelta(days=5))
        self.assertTrue('event_ids' in backend.redis.expiry)
        self.assertEqual(backend.redis.expiry['event_ids'], timedelta(days=5))

    def test_flush_does_not_write_dups(self):
        '''
        flush only writes items from add buffers
        given: a backend instance
        when: flush is called
        and when: add buffers are not empty
        then: the backend cache is updated with ONLY the items from the add buffers
        '''

        # setup
        backend = BackendStub({
            'foo': set(['bar', 'baz']),
            'beep': 1,
            'boop': 1,
            'event_ids': set(['beep', 'boop'])
        })
        line1 = { 'REQUEST_ID': 'bip' }
        line2 = { 'REQUEST_ID': 'bop' }

        # execute
        data_cache = cache.DataCache(backend, 5)
        data_cache.check_or_set_log_line('foo', line1)
        data_cache.check_or_set_log_line('foo', line2)
        data_cache.check_or_set_event_id('bim')
        data_cache.check_or_set_event_id('bam')
        data_cache.flush()

        # verify
        self.assertEqual(len(backend.redis.test_cache), 6)
        self.assertTrue('foo' in backend.redis.test_cache)
        self.assertEqual(
            backend.redis.test_cache['foo'],
            set(['bar', 'baz', 'bip', 'bop']),
        )
        self.assertTrue('event_ids' in backend.redis.test_cache)
        self.assertEqual(
            backend.redis.test_cache['event_ids'],
            set(['beep', 'boop', 'bim', 'bam']),
        )
        self.assertTrue('bim' in backend.redis.expiry)
        self.assertEqual(backend.redis.expiry['bim'], timedelta(days=5))
        self.assertTrue('bam' in backend.redis.expiry)
        self.assertEqual(backend.redis.expiry['bam'], timedelta(days=5))

    def test_flush_raises_if_backend_does(self):
        '''
        flush raises CacheException if backend raises any Exception
        given: a backend instance
        when: flush is called
        and when: backend raises any exception
        then: a CacheException is raised
        '''

        # setup
        backend = BackendStub({})

        # execute / verify
        data_cache = cache.DataCache(backend, 5)

        # have to add data to be cached before setting raise_error
        data_cache.check_or_set_event_id('foo')

        # now set error and execute/verify
        backend.redis.raise_error = True

        with self.assertRaises(CacheException) as _:
            data_cache.flush()


class TestCacheFactory(unittest.TestCase):
    def test_new_returns_none_if_disabled(self):
        '''
        new returns None if cache disabled
        given: a backend factory and a configuration
        when: new is called
        and when: cache_enabled is False in config
        then: None is returned
        '''

        # setup
        config = mod_config.Config({ 'cache_enabled': 'false' })
        backend_factory = BackendFactoryStub()

        # execute
        cache_factory = cache.CacheFactory(backend_factory)
        data_cache = cache_factory.new(config)

        # verify
        self.assertIsNone(data_cache)

    def test_new_returns_data_cache_with_backend_if_enabled(self):
        '''
        new returns DataCache instance with backend from specified backend factory if cache enabled
        given: a backend factory and a configuration
        when: new is called
        and when: cache_enabled is True in config
        then: a DataCache is returned with the a backend from the specified backend factory
        '''

        # setup
        config = mod_config.Config({ 'cache_enabled': 'true' })
        backend_factory = BackendFactoryStub()

        # execute
        cache_factory = cache.CacheFactory(backend_factory)
        data_cache = cache_factory.new(config)

        # verify
        self.assertIsNotNone(data_cache)
        self.assertTrue(type(data_cache.backend) is BackendStub)

    def test_new_raises_if_backend_factory_does(self):
        '''
        new raises CacheException if backend factory does
        given: a backend factory and a configuration
        when: new is called
        and when: backend factory new() raises any exception
        then: a CacheException is raised
        '''

        # setup
        config = mod_config.Config({ 'cache_enabled': 'true' })
        backend_factory = BackendFactoryStub(raise_error=True)

        # execute / verify
        cache_factory = cache.CacheFactory(backend_factory)

        with self.assertRaises(CacheException):
            _ = cache_factory.new(config)
