package common

import (
	"time"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

const (
	// gRPC server constants
	GRPCEndpoint    = "api.pubsub.salesforce.com:7443"
	GRPCDialTimeout = 5 * time.Second
	GRPCCallTimeout = 5 * time.Second
)

var (
	// Number of events to ask for. Read from the config file or 10 if not specified
	Appetite int32 = 0

	// OAuth credentials
	Auth config.AuthConfig
)

func SetCredentials(auth config.AuthConfig) {
	Auth = auth
}

func SetAppetite(appetite int32) {
	Appetite = appetite
}
