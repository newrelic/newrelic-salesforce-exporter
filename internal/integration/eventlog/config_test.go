package eventlog

import (
	"testing"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

func validCache() *config.CacheConfig {
	return &config.CacheConfig{
		Redis: &config.RedisConfig{
			Host:       "host",
			Port:       100,
			DbNumber:   0,
			Password:   "password",
			ExpireDays: 0,
		},
	}
}

func validAuth() config.AuthConfig {
	return config.AuthConfig{
		TokenUrl: "http://example.com",
		UserPass: &config.UserPassAuth{
			ClientId:     "client_id",
			ClientSecret: "client_secret",
			Username:     "username",
			Password:     "password",
		},
	}
}

func validEventlogConf(name string) *config.EventLogConfig {
	return &config.EventLogConfig{
		Name:                name,
		ApiVer:              "",
		Auth:                validAuth(),
		Cache:               &config.CacheConfig{},
		EventTypes:          []string{},
		FieldMappingFile:    "",
		FieldMapping:        config.FieldMappingConfig{},
		InitialTimeInterval: config.TimeIntervalConfig{},
		SkipLogFiles:        false,
		CustomQueryFiles:    []string{},
		CustomQueries:       []config.QueryConfig{},
		RequestTimeout:      0,
		Limits:              config.LimitsConfig{},
	}
}

func TestIntegrityCheck(t *testing.T) {
	conf := config.Config{}
	err := IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty config")
	}

	conf.EventLog = &config.EventLogConfig{}
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log config")
	}

	conf.EventLog = validEventlogConf("my-instance-1")
	err = IntegrityCheck(&conf)
	if err != nil {
		t.Errorf("Integrity check didn't accept a valid event log config")
	}

	conf.EventLog.Cache = validCache()
	err = IntegrityCheck(&conf)
	if err != nil {
		t.Errorf("Integrity didn't accept a valid event log cache config")
	}

	conf.EventLog.Cache.Redis.Host = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log cache host")
	}

	conf.EventLog.Auth = validAuth()

	conf.EventLog.Auth.TokenUrl = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log auth token url")
	}

	conf.EventLog.Auth.TokenUrl = "hello"
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an invalid event log auth token url")
	}

	conf.EventLog.Auth = validAuth()

	conf.EventLog.Auth.UserPass.ClientId = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log auth client id")
	}

	conf.EventLog.Auth = validAuth()

	conf.EventLog.Auth.UserPass.ClientSecret = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log auth client secret")
	}

	conf.EventLog.Auth = validAuth()

	conf.EventLog.Auth.UserPass.Password = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log auth password")
	}

	conf.EventLog.Auth = validAuth()

	conf.EventLog.Auth.UserPass.Username = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log auth username")
	}
}
