package redis

import (
	"context"
	"strconv"
	"time"

	"github.com/redis/go-redis/v9"
)

type RedisConfig struct {
	Host string
  	Port int
  	DbNumber int
  	Password string
  	ExpireDays int
}

type RedisCache struct {
	Conf RedisConfig
	Client *redis.Client
}

// Implement Cache interface for Redis

func (c *RedisCache) GetCacheVal(key string) (any, error) {
	ctx := context.Background()
	val, err := c.Client.Get(ctx, key).Result()
	if err == redis.Nil {
		return nil, nil
	} else {
		return val, err
	}
}

func (c *RedisCache) SetCacheVal(key string, val any) error {
	ctx := context.Background()
	err := c.Client.Set(ctx, key, val, time.Duration(c.Conf.ExpireDays * 24) * time.Hour).Err()
	return err
}

func (c *RedisCache) DelCacheVal(key string) error {
	ctx := context.Background()
	err := c.Client.Del(ctx, key).Err()
	return err
}

// Create new Redis cache object

func NewRedisCache(conf RedisConfig) RedisCache {
	client := redis.NewClient(&redis.Options{
        Addr:     conf.Host + ":" + strconv.Itoa(conf.Port),
        Password: conf.Password,
        DB:       conf.DbNumber,
    })
	//TODO: how to set SSL?
	return RedisCache{
		Conf: conf,
		Client: client,
	}
}