package common

import (
	"time"
)

const (
	// Number of events to ask for
	Appetite int32 = 10

	// gRPC server constants
	GRPCEndpoint    = "api.pubsub.salesforce.com:7443"
	GRPCDialTimeout = 5 * time.Second
	GRPCCallTimeout = 5 * time.Second

	// OAuth server constants
	OAuthDialTimeout = 5 * time.Second
)

var (
	// OAuth variables
	GrantType     string
	ClientId      string
	ClientSecret  string
	Username      string
	Password      string
	TokenEndpoint string
)