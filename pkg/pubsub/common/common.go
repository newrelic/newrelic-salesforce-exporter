package common

import (
	"time"

	"github.com/newrelic/newrelic-salesforce-exporter/pkg/pubsub/proto"
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

	ReplayPreset = proto.ReplayPreset_LATEST
	//TODO: get replay ID from a database, one per topic
	ReplayId []byte = nil
	//TODO: set the number of events to ask for in the config file
	Appetite int32 = 1

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
