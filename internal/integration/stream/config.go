package stream

import (
	"errors"
	"fmt"
	"os"
	"reflect"

	"regexp"

	"github.com/go-viper/mapstructure/v2"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration"
	labslog "github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache/redis"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/common"
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

func envVarDecoder() mapstructure.DecodeHookFunc {
	return func(
		f reflect.Type,
		t reflect.Type,
		data any,
	) (any, error) {
		if t == reflect.TypeOf(Config{}) {
			scanEnvVars(data.(map[string]any))
			return data, nil			
		} else {
			return data, nil
		}
	}
}

// Check if the value of a field is an env var "$VAR_NAM", and read it.
func scanEnvVars(dict map[string]any) {
	for key, val := range dict {
		switch val := val.(type) {
		case map[string]any:
			scanEnvVars(val)
		case string:
			var re = regexp.MustCompile(`^\$[a-zA-Z_]+[a-zA-Z0-9_]*`)
			loc := re.FindStringIndex(val)
			// Regex is a full match
			isEnvVar := len(loc) == 2 && (loc[0] == 0 && loc[1] == len(val))
			if isEnvVar {
				varName := val[1:]
				envVal, exists := os.LookupEnv(varName)
				if exists {
					dict[key] = envVal
				} else {
					labslog.Fatalf(errors.New(fmt.Sprintf("Env var %s does not exist", varName)))
				}
			}
		}
	}
}

func ReadConfig(file string) (Config, error) {
	if err := integration.NewConfigWithFile(file); err != nil {
		return Config{}, err
	}

	conf := Config{}

	decoderConf := viper.DecodeHook(
		mapstructure.ComposeDecodeHookFunc(
			envVarDecoder(),
		),
	)
	
	if err := viper.Unmarshal(&conf, decoderConf); err != nil {
		return Config{}, err
	}

	if conf.IsTemplate {
		labslog.Fatalf(errors.New("Config file is a template"))
	}

	//TODO: check config integrity

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