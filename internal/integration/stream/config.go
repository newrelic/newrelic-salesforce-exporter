package stream

import (
	"github.com/newrelic/newrelic-salesforce-exporter/internal"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/common"
)

func FillSalesforceCredentials(conf internal.Config) {
	common.GrantType = "password"
	common.ClientId = conf.EventStream.Auth.UserPass.ClientId
	common.ClientSecret = conf.EventStream.Auth.UserPass.ClientSecret
	common.Username = conf.EventStream.Auth.UserPass.Username
	common.Password = conf.EventStream.Auth.UserPass.Password
	common.TokenEndpoint = conf.EventStream.Auth.TokenUrl
}
