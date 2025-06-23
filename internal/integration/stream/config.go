package stream

import (
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/common"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
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
func CheckConfig(conf config.Config) error {
	if err := config.CheckAuth(conf.EventStream.Auth) ; err != nil {
		return err
	}
	if err := config.CheckUserPassCredentials(conf.EventStream.Auth.UserPass) ; err != nil {
		return err
	}
	if conf.EventStream.Cache == nil {
		log.Warnf("Cache not defined, events won't be de-duplicated.")
	}
	return nil
}
