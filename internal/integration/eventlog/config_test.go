package eventlog

import (
	"testing"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

func validCache() *config.CacheConfig {
	return &config.CacheConfig{
		Redis: &config.RedisConfig{
			Host: "host",
			Port: 100,
			DbNumber: 0,
			Password: "password",
			ExpireDays: 0,
		},
	}
}

func validAuth() config.AuthConfig {
	return config.AuthConfig{
		TokenUrl: "http://example.com",
		UserPass: &config.UserPassAuth{
			ClientId: "client_id",
			ClientSecret: "client_secret",
			Username: "username",
			Password: "password",
		},
	}
}

func validEventLogInstance(name string) config.EventLogInstance {
	return config.EventLogInstance{
		Name: name,
		ApiVer: "",
		Auth: validAuth(),
		Cache: &config.CacheConfig{},
		EventTypes: []string{},
		FieldMappingFile: "",
    	FieldMapping: config.FieldMappingConfig{},
		InitialTimeInterval: config.TimeIntervalConfig{},
		SkipLogFiles: false,
		CustomQueryFiles: []string{},
		CustomQueries: []config.QueryConfig{},
		RequestTimeout: 0,
		Limits: config.LimitsConfig{},
	}
}

func validEventlogConf(instances ...config.EventLogInstance) *config.EventLogConfig {
	return &config.EventLogConfig {
		IntegrationName: "my.integration.name",
		RequestTimeout: 10,
		Instances: instances,
	}
}

func TestIntegrityCheckMinConfig(t *testing.T) {
	conf := config.Config{
		EventLog: validEventlogConf(validEventLogInstance("my-instance-1")),
	}
		
	err := IntegrityCheck(&conf)
	if err != nil {
		t.Errorf("Failed on a correct config: %s", err)
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

	conf.EventLog = validEventlogConf(validEventLogInstance("my-instance-1"))
	err = IntegrityCheck(&conf)
	if err != nil {
		t.Errorf("Integrity check didn't accept a valid event log config")
	}

	conf.EventLog.IntegrationName = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log integration name")
	}

	conf.EventLog.IntegrationName = "my.integration.name"

	conf.EventLog.Instances[0].Cache = validCache()
	err = IntegrityCheck(&conf)
	if err != nil {
		t.Errorf("Integrity didn't accept a valid event log cache config")
	}

	conf.EventLog.Instances[0].Cache.Redis.Host = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log cache host")
	}

	conf.EventLog.Instances[0].Auth = validAuth()

	conf.EventLog.Instances[0].Auth.TokenUrl = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log auth token url")
	}

	conf.EventLog.Instances[0].Auth.TokenUrl = "hello"
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an invalid event log auth token url")
	}

	conf.EventLog.Instances[0].Auth = validAuth()

	conf.EventLog.Instances[0].Auth.UserPass.ClientId = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log auth client id")
	}

	conf.EventLog.Instances[0].Auth = validAuth()

	conf.EventLog.Instances[0].Auth.UserPass.ClientSecret = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log auth client secret")
	}

	conf.EventLog.Instances[0].Auth = validAuth()

	conf.EventLog.Instances[0].Auth.UserPass.Password = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log auth password")
	}

	conf.EventLog.Instances[0].Auth = validAuth()

	conf.EventLog.Instances[0].Auth.UserPass.Username = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event log auth username")
	}

	conf = config.Config{
		EventLog: validEventlogConf(
			validEventLogInstance("my-instance-1"),
			validEventLogInstance("my-instance-1"),
		),
	}
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch a duplicated instance name")
	}
}