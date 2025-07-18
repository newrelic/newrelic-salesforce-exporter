package eventlog

import (
	"errors"
	"fmt"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

// Config checks specific to the event log integration
func IntegrityCheck(conf config.Config) error {
	if conf.EventLog == nil {
		return errors.New("Config eventLog must be defined")
	}
	if len(conf.EventLog.Instances) == 0 {
		return errors.New("Config eventLog->instances must contain at least one instance")
	}
	instanceNames := map[string]bool{}
	for _, instance := range conf.EventLog.Instances {
		_, ok := instanceNames[instance.Name]
		if ok {
			return fmt.Errorf("Instance name '%s' is duplicated. Instances names must be unique.", instance.Name)
		} else {
			instanceNames[instance.Name] = true
		}
		if err := config.CheckAuth(instance.Auth) ; err != nil {
			return err
		}
		//TODO: check JWT credentials
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
	}

	return nil
}