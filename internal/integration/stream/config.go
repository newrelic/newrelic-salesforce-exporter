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
	if conf.EventStream.Name == "" {
		return errors.New("Config eventStream instanceName must be defined")
	}
	if err := CheckAuth(&conf.EventStream.Auth); err != nil {
		return err
	}
	if err := config.CheckCache(conf.EventStream.Cache); err != nil {
		return err
	}
	if err := checkTopics(conf.EventStream.Topics); err != nil {
		return err
	}
	return nil
}

func CheckAuth(auth *config.AuthConfig) error {
	if auth.TokenUrl == "" {
		return errors.New("Empty 'auth.tokenUrl'")
	}
	if !config.CheckUrl(auth.TokenUrl) {
		return errors.New("Invalid URL 'auth.tokenUrl'")
	}
	if auth.Jwt != nil {
		return errors.New("Invalid auth method, only userPass is supported")
	}
	if auth.ClientCred != nil {
		return errors.New("Invalid auth method, only userPass is supported")
	}
	if auth.UserPass != nil {
		err := config.CheckUserPassCredentials(auth.UserPass)
		if err != nil {
			return err
		}
	} else {
		return errors.New("Authentication credentials undefined")
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
