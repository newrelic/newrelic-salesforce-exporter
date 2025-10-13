package eventlog

import (
	"testing"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

func defaultCache() *config.CacheConfig {
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

func defaultAuth() config.AuthConfig {
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

func defaultEventLogInstance(name string) config.EventLogInstance {
	return config.EventLogInstance{
		Name: name,
		ApiVer: "",
		Auth: defaultAuth(),
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

func defaultEventlogConf(instances ...config.EventLogInstance) *config.EventLogConfig {
	return &config.EventLogConfig {
		IntegrationName: "my.integration.name",
		RequestTimeout: 10,
		Instances: instances,
	}
}

func TestIntegrityCheckMinConfig(t *testing.T) {
	conf := config.Config{
		Version: "2.0",
		EventLog: defaultEventlogConf(defaultEventLogInstance("my-instance-1")),
		Format: "events",
	}
		
	err := IntegrityCheck(&conf)
	if err != nil {
		t.Errorf("Failed on a correct config: %s", err)
	}
}