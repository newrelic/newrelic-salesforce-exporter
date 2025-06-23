package cache

import (
	labslog "github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache/redis"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

type Cache interface {
	GetCacheVal(key string) (any, error)
	SetCacheVal(key string, val any) error
	DelCacheVal(key string) error
}

type DummyCache struct {}

func (c *DummyCache) GetCacheVal(key string) (any, error) {
	return nil, nil
}

func (c *DummyCache) SetCacheVal(key string, val any) error {
	return nil
}

func (c *DummyCache) DelCacheVal(key string) error {
	return nil
}

func BuildCache(conf *config.CacheConfig) Cache {
	var db Cache
	if conf != nil {
		if conf.Redis != nil {
			labslog.Debugf("Using Redis cache")
			redisDb := redis.NewRedisCache(redis.RedisConfig{
				Host: conf.Redis.Host,
				Port: conf.Redis.Port,
				DbNumber: conf.Redis.DbNumber,
				Password: conf.Redis.Password,
				ExpireDays: conf.Redis.ExpireDays,
			})
			db = &redisDb
		} else {
			db = &DummyCache{}
		}
	} else {
		db = &DummyCache{}
	}

	return db
}