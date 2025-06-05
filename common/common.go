package common

import (
	"time"

	"github.com/newrelic/newrelic-salesforce-exporter/proto"
)

var (
	//TODO: get tipics from config file

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

	ReplayPreset = proto.ReplayPreset_LATEST
	//TODO: set a different ReplayId per topic.
	ReplayId []byte = nil
	Appetite int32  = 1

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
