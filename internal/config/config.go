package config

import (
	"errors"
	"fmt"
	"os"
	"reflect"

	"regexp"

	"github.com/go-viper/mapstructure/v2"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/spf13/viper"
)

type AuthConfig struct {
	TokenUrl string        `mapstructure:"token_url"`
	UserPass *UserPassAuth `mapstructure:"user_pass"`
}

type UserPassAuth struct {
	ClientId     string `mapstructure:"client_id"`
	ClientSecret string `mapstructure:"client_secret"`
	Username     string `mapstructure:"username"`
	Password     string `mapstructure:"password"`
}

type CacheConfig struct {
	Redis *RedisConfig `mapstructure:"redis"`
}

type RedisConfig struct {
	Host       string `mapstructure:"host"`
	Port       int    `mapstructure:"port"`
	DbNumber   int    `mapstructure:"db_number"`
	Password   string `mapstructure:"password"`
	Ssl        bool   `mapstructure:"ssl"`
	ExpireDays int    `mapstructure:"expire_days"`
}

type EventStreamConfig struct {
	IntegrationName string       `mapstructure:"integration_name"`
	Auth            AuthConfig   `mapstructure:"auth"`
	Cache           *CacheConfig `mapstructure:"cache"`
	Topics          []string     `mapstructure:"topics"`
}

type Config struct {
	Version     string            `mapstructure:"version"`
	IsTemplate  bool              `mapstructure:"is_template"`
	EventStream EventStreamConfig `mapstructure:"event_stream"`
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
					log.Fatalf(fmt.Errorf("Env var %s does not exist", varName))
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

	if err := integrityCheck(conf); err != nil {
		log.Fatalf(err)
	}

	return conf, nil
}

// Check config integrity, the parts that are common to both integrations
func integrityCheck(conf Config) error {
	if conf.IsTemplate {
		return errors.New("Config file is a template")
	}
	return nil
}
