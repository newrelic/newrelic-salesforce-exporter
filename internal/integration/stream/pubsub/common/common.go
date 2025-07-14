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
)