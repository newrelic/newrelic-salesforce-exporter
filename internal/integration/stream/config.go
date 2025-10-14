package stream

import (
	"errors"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

// Config checks specific to the event stream integration
func IntegrityCheck(conf *config.Config) error {
	if conf.EventStream == nil {
		return errors.New("Config eventStream must be defined")
	}
	if conf.EventStream.IntegrationName == "" {
		return errors.New("Config eventStream integrationName must be defined")
	}
	if err := config.CheckAuth(&conf.EventStream.Auth) ; err != nil {
		return err
	}
	if err := config.CheckCache(conf.EventStream.Cache) ; err != nil {
		return err
	}
	if err := checkTopics(conf.EventStream.Topics) ; err != nil {
		return err
	}
	return nil
}

func checkTopics(topics []string) error {
	if topics == nil {
		return errors.New("'eventStream.topics' must be a list of strings")
	}
	if len(topics) == 0 {
		return errors.New("Empty 'eventStream.topics'")
	}
	return nil
}