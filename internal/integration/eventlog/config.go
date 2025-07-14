package eventlog

import (
	"errors"

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
	for _, instance := range conf.EventLog.Instances {
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
	}

	return nil
}