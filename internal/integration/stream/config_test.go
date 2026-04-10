package stream

import (
	"testing"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

func rightStreamConf() *config.EventStreamConfig {
	return &config.EventStreamConfig{
		Name: "my-instance-name",
		Auth: config.AuthConfig{
			TokenUrl: "http://example.com",
			UserPass: &config.UserPassAuth{
				ClientId:     "client_id",
				ClientSecret: "client_secret",
				Username:     "username",
				Password:     "password",
			},
		},
		Cache: &config.CacheConfig{
			Redis: &config.RedisConfig{
				Host:       "host",
				Port:       100,
				DbNumber:   0,
				Password:   "password",
				ExpireDays: 0,
			},
		},
		Appetite: 10,
		Topics: []string{
			"one", "two", "three",
		},
	}
}

func TestIntegrityCheck(t *testing.T) {
	conf := config.Config{}
	err := IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty config")
	}

	conf.EventStream = &config.EventStreamConfig{}
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event stream config")
	}

	conf.EventStream = rightStreamConf()
	err = IntegrityCheck(&conf)
	if err != nil {
		t.Errorf("Integrity check didn't accept a valid event stream config")
	}

	conf.EventStream.Name = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event stream instance name")
	}

	conf.EventStream = rightStreamConf()

	conf.EventStream.Appetite = 0
	err = IntegrityCheck(&conf)
	if err != nil {
		t.Errorf("Integrity check didn't accept a valid event stream appetite")
	}

	conf.EventStream = rightStreamConf()

	conf.EventStream.Cache.Redis.Host = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event stream cache host")
	}

	conf.EventStream = rightStreamConf()

	conf.EventStream.Auth.TokenUrl = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event stream auth token url")
	}

	conf.EventStream.Auth.TokenUrl = "hello"
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an invalid event stream auth token url")
	}

	conf.EventStream = rightStreamConf()

	conf.EventStream.Auth.UserPass.ClientId = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event stream auth client id")
	}

	conf.EventStream = rightStreamConf()

	conf.EventStream.Auth.UserPass.ClientSecret = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event stream auth client secret")
	}

	conf.EventStream = rightStreamConf()

	conf.EventStream.Auth.UserPass.Password = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event stream auth password")
	}

	conf.EventStream = rightStreamConf()

	conf.EventStream.Auth.UserPass.Username = ""
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event stream auth username")
	}

	conf.EventStream = rightStreamConf()

	conf.EventStream.Topics = []string{}
	err = IntegrityCheck(&conf)
	if err == nil {
		t.Errorf("Integrity check didn't catch an empty event stream topics list")
	}
}
