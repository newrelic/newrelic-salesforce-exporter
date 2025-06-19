package stream

import (
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration"
	labslog "github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache/redis"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/pubsub/common"
	"github.com/spf13/viper"
)

type Config struct {
	Version    string `mapstructure:"version"`
	IsTemplate bool   `mapstructure:"is_template"`

	EventStream struct {
		IntegrationName string `mapstructure:"integration_name"`
		Auth            struct {
			TokenUrl string `mapstructure:"token_url"`
			UserPass struct {
				ClientId     string `mapstructure:"client_id"`
				ClientSecret string `mapstructure:"client_secret"`
				Username     string `mapstructure:"username"`
				Password     string `mapstructure:"password"`
			} `mapstructure:"user_pass"`
		} `mapstructure:"auth"`
		Cache *struct {
			Redis *struct {
				Host string `mapstructure:"host"`
				Port int `mapstructure:"port"`
				DbNumber int `mapstructure:"db_number"`
				Password string `mapstructure:"password"`
				Ssl bool `mapstructure:"ssl"`
				ExpireDays int `mapstructure:"expire_days"`
			} `mapstructure:"redis"`
		} `mapstructure:"cache"`
		Topics []string `mapstructure:"topics"`
	} `mapstructure:"event_stream"`
}

// TODO: explore how viper loads config from env variables
func ReadConfig(file string) (Config, error) {
	if err := integration.NewConfigWithFile(file); err != nil {
		return Config{}, err
	}

	conf := Config{}

	if err := viper.Unmarshal(&conf); err != nil {
		return Config{}, err
	}

	//TODO: check conf integrity

	return conf, nil
}

func FillSalesforceCredentials(conf Config) {
	common.GrantType = "password"
	common.ClientId = conf.EventStream.Auth.UserPass.ClientId
	common.ClientSecret = conf.EventStream.Auth.UserPass.ClientSecret
	common.Username = conf.EventStream.Auth.UserPass.Username
	common.Password = conf.EventStream.Auth.UserPass.Password
	common.TokenEndpoint = conf.EventStream.Auth.TokenUrl
}

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