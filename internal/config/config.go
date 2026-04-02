package config

import (
	"errors"
	"fmt"
	"os"
	"reflect"
	"strconv"
	"strings"

	"regexp"

	"github.com/go-viper/mapstructure/v2"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/spf13/viper"
)

type AuthConfig struct {
	TokenUrl   string          `mapstructure:"tokenUrl"`
	UserPass   *UserPassAuth   `mapstructure:"userPass"`
	Jwt        *JwtAuth        `mapstructure:"jwt"`
	ClientCred *ClientCredAuth `mapstructure:"clientCred"`
}

type UserPassAuth struct {
	ClientId     string `mapstructure:"clientId"`
	ClientSecret string `mapstructure:"clientSecret"`
	Username     string `mapstructure:"username"`
	Password     string `mapstructure:"password"`
}

type JwtAuth struct {
	ClientId   string `mapstructure:"clientId"`
	PrivateKey string `mapstructure:"privateKey"`
	Username   string `mapstructure:"username"`
}

type ClientCredAuth struct {
	ClientId     string `mapstructure:"clientId"`
	ClientSecret string `mapstructure:"clientSecret"`
}

type CacheConfig struct {
	Redis *RedisConfig `mapstructure:"redis"`
}

type RedisConfig struct {
	Host       string `mapstructure:"host"`
	Port       uint   `mapstructure:"port"`
	DbNumber   uint   `mapstructure:"dbNumber"`
	Password   string `mapstructure:"password"`
	ExpireDays uint   `mapstructure:"expireDays"`
}

type EventStreamConfig struct {
	//TODO: remove integrationName
	IntegrationName string       `mapstructure:"integrationName"`
	Auth            AuthConfig   `mapstructure:"auth"`
	Cache           *CacheConfig `mapstructure:"cache"`
	Appetite        int32        `mapstructure:"appetite"`
	Topics          []string     `mapstructure:"topics"`
}

type FieldNames = []string
type FieldMappingConfig = map[string]FieldNames

type FieldMappingFileModel struct {
	Mapping FieldMappingConfig `mapstructure:"mapping"`
}

type LimitsConfig struct {
	ApiVer string   `mapstructure:"apiVer"`
	Names  []string `mapstructure:"names"`
}

type ExternalQueryFileConfig struct {
	Queries []QueryConfig `mapstructure:"queries"`
}

type QueryConfig struct {
	Soql         SoqlConfig `mapstructure:"soql"`
	ApiVer       string     `mapstructure:"apiVer"`
	Timestamp    string     `mapstructure:"timestamp"`
	EndTimestamp string     `mapstructure:"endTimestamp"`
	ApiName      string     `mapstructure:"apiName"`
}

type SoqlConfig struct {
	Select []string `mapstructure:"select"`
	From   string   `mapstructure:"from"`
	Where  string   `mapstructure:"where"`
	Tail   string   `mapstructure:"tail"`
}

type TimeIntervalConfig struct {
	Hours   uint `mapstructure:"hours"`
	Minutes uint `mapstructure:"minutes"`
}

type EventLogConfig struct {
	Name                string             `mapstructure:"instanceName"`
	ApiVer              string             `mapstructure:"apiVer"`
	RequestTimeout      uint               `mapstructure:"requestTimeout"`
	Auth                AuthConfig         `mapstructure:"auth"`
	Cache               *CacheConfig       `mapstructure:"cache"`
	EventTypes          []string           `mapstructure:"eventTypes"`
	FieldMappingFile    string             `mapstructure:"fieldMappingFile"`
	FieldMapping        FieldMappingConfig `mapstructure:"fieldMapping"`
	InitialTimeInterval TimeIntervalConfig `mapstructure:"initialTimeInterval"`
	SkipLogFiles        bool               `mapstructure:"skipLogFiles"`
	SkipLimits          bool               `mapstructure:"skipLimits"`
	NoInterval          bool               `mapstructure:"noInterval"`
	CustomQueryFiles    []string           `mapstructure:"customQueryFiles"`
	CustomQueries       []QueryConfig      `mapstructure:"customQueries"`
	Limits              LimitsConfig       `mapstructure:"limits"`
}

type Config struct {
	Version     string             `mapstructure:"version"`
	IsTemplate  bool               `mapstructure:"isTemplate"`
	EventStream *EventStreamConfig `mapstructure:"eventStream"`
	EventLog    *EventLogConfig    `mapstructure:"eventLog"`
	Format      string             `mapstructure:"format"`
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

func ReadConfig() (Config, error) {
	conf := Config{}
	decoderConf := viper.DecodeHook(
		mapstructure.ComposeDecodeHookFunc(
			envVarDecoder(),
		),
	)
	if err := viper.Unmarshal(&conf, decoderConf); err != nil {
		return Config{}, err
	}

	if err := integrityCheck(&conf); err != nil {
		log.Fatalf(err)
	}

	return conf, nil
}

// Check config integrity, the parts that are common to both integrations
func integrityCheck(conf *Config) error {
	if conf.IsTemplate {
		return errors.New("Config file is a template")
	}
	verCompos := strings.Split(conf.Version, ".")
	if len(verCompos) != 2 {
		return errors.New("Conf file, version key must be 'X.Y'")
	}
	major, err := strconv.Atoi(verCompos[0])
	if err != nil {
		return errors.New("Conf file, wrong version key format, major must be a number")
	}
	minor, err := strconv.Atoi(verCompos[1])
	if err != nil {
		return errors.New("Conf file, wrong version key format, minor must be a number")
	}
	if major != 2 {
		return fmt.Errorf("Conf file major version is '%d', expected '2'", major)
	}
	if minor != 0 {
		log.Warnf("Conf file minor version is '%d', expected '0'", minor)
	}
	if conf.Format != "logs" && conf.Format != "events" {
		return fmt.Errorf("Conf format must be either 'logs' or 'events'")
	}
	return nil
}
