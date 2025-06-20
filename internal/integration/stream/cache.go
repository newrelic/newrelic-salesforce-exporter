package stream

import (
	labslog "github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache/redis"
)

func BuildCache(conf Config) cache.Cache {
	var db cache.Cache
	if conf.EventStream.Cache != nil {
		if conf.EventStream.Cache.Redis != nil {
			labslog.Debugf("Using Redis cache")
			redisDb := redis.NewRedisCache(redis.RedisConfig{
				Host: conf.EventStream.Cache.Redis.Host,
				Port: conf.EventStream.Cache.Redis.Port,
				DbNumber: conf.EventStream.Cache.Redis.DbNumber,
				Password: conf.EventStream.Cache.Redis.Password,
				ExpireDays: conf.EventStream.Cache.Redis.ExpireDays,
			})
			db = &redisDb
		} else {
			db = &cache.DummyCache{}
		}
	} else {
		db = &cache.DummyCache{}
	}

	return db
}