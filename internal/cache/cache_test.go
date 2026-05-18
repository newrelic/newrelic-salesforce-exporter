package cache

import (
	"testing"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache/redis"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

func TestBuildCache(t *testing.T) {
	{
		config := &config.CacheConfig{
			Redis: &config.RedisConfig{},
		}
		cache := BuildCache(config)
		_, ok := cache.(*redis.RedisCache)
		if !ok {
			t.Errorf("Expected a RedisCache object from BuildCache")
		}
	}

	{
		config := &config.CacheConfig{}
		cache := BuildCache(config)
		_, ok := cache.(*DummyCache)
		if !ok {
			t.Errorf("Expected a DummyCache object from BuildCache")
		}
	}
}
