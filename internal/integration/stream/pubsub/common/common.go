package common

import (
	"time"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

const (
	// Number of events to ask for
	Appetite int32 = 10

	// gRPC server constants
	GRPCEndpoint    = "api.pubsub.salesforce.com:7443"
	GRPCDialTimeout = 5 * time.Second
	GRPCCallTimeout = 5 * time.Second
)

var (
	// OAuth credentials
	GrantType     string
	ClientId      string
	ClientSecret  string
	Username      string
	Password      string
	TokenEndpoint string
)

func FillCredentials(auth config.AuthConfig) {
	GrantType = "password"
	ClientId = auth.UserPass.ClientId
	ClientSecret = auth.UserPass.ClientSecret
	Username = auth.UserPass.Username
	Password = auth.UserPass.Password
	TokenEndpoint = auth.TokenUrl
}