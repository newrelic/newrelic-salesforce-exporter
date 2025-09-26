package eventlog

import (
	"errors"
	"fmt"
	"strings"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

// Default request timeout
const defaultTimeout = 5

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
		if err := config.CheckAuth(&instance.Auth) ; err != nil {
			return err
		}
		if err := config.CheckUserPassCredentials(instance.Auth.UserPass) ; err != nil {
			return err
		}
		if err := config.CheckCache(instance.Cache) ; err != nil {
			return err
		}
		if instance.ApiVer == "" {
			log.Warnf("Config 'apiVer' not defined, using default: '55.0'")
			instance.ApiVer = "55.0"
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
			if customQuery.Soql.From == "" {
				return fmt.Errorf("All custom queries must contain a SOQL 'from' definition")
			}
			if len(customQuery.Soql.Select) == 0 {
				return fmt.Errorf("All custom queries must contain at least one SOQL 'select' attribute")
			}
		}
	}

	return nil
}