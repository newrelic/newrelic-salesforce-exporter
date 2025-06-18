package common

import (
	"time"
)

var (
	//TODO: set topics in the config file

	// topic and subscription-related variables
	Topics = []string{
		"/event/LoginEventStream",
		//"/event/LogoutEventStream",
		//"/event/ReportEventStream",
		"/event/ApiEventStream",
		//"/event/FileEvent",
		//"/event/UriEventStream",
		//"/event/LightningUriEventStream",
	}

	Appetite int32 = 10

	// gRPC server variables
	GRPCEndpoint    = "api.pubsub.salesforce.com:7443"
	GRPCDialTimeout = 5 * time.Second
	GRPCCallTimeout = 5 * time.Second

	// OAuth header variables
	GrantType    string
	ClientId     string
	ClientSecret string
	Username     string
	Password     string

	// OAuth server variables
	OAuthEndpoint    string
	OAuthDialTimeout = 5 * time.Second
)
