package eventlog

import (
	"errors"
	"fmt"
	"strings"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
	"github.com/spf13/viper"
)

const (
	defaultApiVer  = "55.0"
	defaultTimeout = 5
	apiNameRest    = "rest"
	apiNameTooling = "tooling"
	defaultApiName = apiNameRest
)

// Config checks specific to the event log integration
func IntegrityCheck(conf *config.Config) error {
	if conf.EventLog == nil {
		return errors.New("Config eventLog must be defined")
	}
	if len(conf.EventLog.Instances) == 0 {
		return errors.New("Config eventLog->instances must contain at least one instance")
	}
	instanceNames := map[string]bool{}
	if conf.EventLog.RequestTimeout == 0 {
		conf.EventLog.RequestTimeout = defaultTimeout
	}
	for instanceIndex := range conf.EventLog.Instances {
		instance := &conf.EventLog.Instances[instanceIndex]
		_, ok := instanceNames[instance.Name]
		if ok {
			return fmt.Errorf("Instance name '%s' is duplicated. Instances names must be unique.", instance.Name)
		} else {
			instanceNames[instance.Name] = true
		}
		if err := config.CheckAuth(&instance.Auth); err != nil {
			return err
		}
		if err := config.CheckUserPassCredentials(instance.Auth.UserPass); err != nil {
			return err
		}
		if err := config.CheckCache(instance.Cache); err != nil {
			return err
		}
		if instance.ApiVer == "" {
			log.Warnf("Config 'apiVer' not defined, using default: '%s'", defaultApiVer)
			instance.ApiVer = defaultApiVer
		}
		if instance.RequestTimeout == 0 {
			instance.RequestTimeout = conf.EventLog.RequestTimeout
		}
		for eventTypeIndex := range instance.EventTypes {
			eventType := &instance.EventTypes[eventTypeIndex]
			if strings.Contains(*eventType, " ") || strings.Contains(*eventType, "+") {
				return fmt.Errorf("Instance '%s' contains an invalid event type: '%s'.", instance.Name, *eventType)
			}
		}
		for customQueryIndex := range instance.CustomQueries {
			customQuery := &instance.CustomQueries[customQueryIndex]
			if customQuery.ApiVer == "" {
				customQuery.ApiVer = instance.ApiVer
			}
			if customQuery.Timestamp == "" {
				return fmt.Errorf("All custom queries must contain a 'timestamp' attribute")
			}
			switch customQuery.ApiName {
			case "":
				customQuery.ApiName = defaultApiName
			case apiNameRest, apiNameTooling:
				// do nothing
			default:
				return fmt.Errorf("The 'apiName' must be either '%s' or '%s'", apiNameRest, apiNameTooling)
			}
			if customQuery.Soql.From == "" {
				return fmt.Errorf("All custom queries must contain a SOQL 'from' definition")
			}
			if len(customQuery.Soql.Select) == 0 {
				return fmt.Errorf("All custom queries must contain at least one SOQL 'select' attribute")
			}
		}
		if instance.Limits.ApiVer == "" {
			instance.Limits.ApiVer = instance.ApiVer
		}
	}

	return nil
}

func ParseQueryFiles(files []string, instanceApiVer string) ([]config.QueryConfig, error) {
	queries := []config.QueryConfig{}
	for index := range files {
		query, err := readExternalQueryConf(files[index])
		if err != nil {
			return nil, fmt.Errorf("Could not read file '%s': %s", files[index], err)
		} else {
			queries = append(queries, query...)
		}
	}
	return queries, nil
}

func ParseMappingFile(file string) (config.FieldMappingConfig, error) {
	localViper := viper.New()
	localViper.SetConfigFile(file)
	err := localViper.ReadInConfig()
	if err != nil {
		return config.FieldMappingConfig{}, err
	}
	mappingConf := config.FieldMappingFileModel{}
	if err := localViper.Unmarshal(&mappingConf); err != nil {
		return config.FieldMappingConfig{}, err
	}
	return mappingConf.Mapping, nil
}

func readExternalQueryConf(file string) ([]config.QueryConfig, error) {
	localViper := viper.New()
	localViper.SetConfigFile(file)
	err := localViper.ReadInConfig()
	if err != nil {
		return nil, err
	}
	queryConf := config.ExternalQueryFileConfig{}
	if err := localViper.Unmarshal(&queryConf); err != nil {
		return nil, err
	}
	return queryConf.Queries, nil
}