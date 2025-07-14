package eventlog

import (
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

// Config checks specific to the event log integration
func IntegrityCheck(conf config.Config) error {
	if err := config.CheckAuth(conf.EventLog.Auth) ; err != nil {
		return err
	}
	//TODO: check JWT credentials
	if err := config.CheckUserPassCredentials(conf.EventLog.Auth.UserPass) ; err != nil {
		return err
	}
	if err := config.CheckCache(conf.EventLog.Cache) ; err != nil {
		return err
	}
	return nil
}