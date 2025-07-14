package stream

import (
	"errors"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/common"
)

func FillSalesforceCredentials(conf config.Config) {
	common.GrantType = "password"
	common.ClientId = conf.EventStream.Auth.UserPass.ClientId
	common.ClientSecret = conf.EventStream.Auth.UserPass.ClientSecret
	common.Username = conf.EventStream.Auth.UserPass.Username
	common.Password = conf.EventStream.Auth.UserPass.Password
	common.TokenEndpoint = conf.EventStream.Auth.TokenUrl
}

// Config checks specific to the event stream integration
func IntegrityCheck(conf config.Config) error {
	if conf.EventStream == nil {
		return errors.New("Config eventStream must be defined")
	}
	if err := config.CheckAuth(conf.EventStream.Auth) ; err != nil {
		return err
	}
	if err := config.CheckUserPassCredentials(conf.EventStream.Auth.UserPass) ; err != nil {
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