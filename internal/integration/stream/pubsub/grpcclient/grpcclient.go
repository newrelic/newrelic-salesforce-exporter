package grpcclient

import (
	"context"
	"crypto/x509"
	"fmt"
	"io"
	"strings"
	"sync"
	"time"

	"github.com/linkedin/goavro/v2"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/common"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/proto"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/oauth"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"

	"encoding/json"
)

const (
	tokenHeader    = "accesstoken"
	instanceHeader = "instanceurl"
	tenantHeader   = "tenantid"
)

var LOGIN_LOCK = LoginLock {}

type LoginLock struct {
	Mutex    		sync.Mutex
	lastAuthTime	time.Time
}

func (ll *LoginLock) ShouldLogin() bool {
	// Last auth was less than 5 minutes ago?
	return ll.lastAuthTime.Before(time.Now().Add(-5*time.Minute))
}

func (ll *LoginLock) DidLogin() {
	ll.lastAuthTime = time.Now()
}

type PubSubClient struct {
	accessToken		string
	instanceURL		string
	userID 			string
	orgID  			string
	conn       		*grpc.ClientConn
	pubSubClient	proto.PubSubClient
	schemaCache		map[string]*goavro.Codec
}

// Closes the underlying connection to the gRPC server
func (c *PubSubClient) Close() {
	c.conn.Close()
}

// Makes a call to the OAuth server to fetch credentials. Credentials are stored as part of the PubSubClient object so that they can be
// referenced later in other methods
func (c *PubSubClient) Authenticate(db cache.Cache) error {
	LOGIN_LOCK.Mutex.Lock()
    defer LOGIN_LOCK.Mutex.Unlock()

    if !LOGIN_LOCK.ShouldLogin() {
		log.Debugf("Recently authenticated, try to use credentials from cache")
		accessToken, _ := db.GetCacheVal("event_stream_access_token")
		instanceUrl, _ := db.GetCacheVal("event_stream_instance_url")
		if accessToken != nil && instanceUrl != nil {
			log.Debugf("Using auth credentials from cache")
			c.accessToken = accessToken.(string)
			c.instanceURL = instanceUrl.(string)
		}
		return nil
	}

	resp, err := oauth.Login(common.Auth)
	if err != nil {
		return err
	}

	c.accessToken = resp.AccessToken
	c.instanceURL = resp.InstanceURL

	db.SetCacheVal("event_stream_access_token", c.accessToken)
	db.SetCacheVal("event_stream_instance_url", c.instanceURL)

	LOGIN_LOCK.DidLogin()

	log.Debugf("Did login")

	return nil
}

// Makes a call to the OAuth server to fetch user info. User info is stored as part of the PubSubClient object so that it can be referenced
// later in other methods
func (c *PubSubClient) FetchUserInfo() error {
	resp, err := oauth.UserInfo(common.Auth.TokenUrl, c.accessToken)
	if err != nil {
		return err
	}

	c.userID = resp.UserID
	c.orgID = resp.OrganizationID

	return nil
}

// Wrapper function around the GetTopic RPC. This will add the OAuth credentials and make a call to fetch data about a specific topic
func (c *PubSubClient) GetTopic(topicName string) (*proto.TopicInfo, error) {
	var trailer metadata.MD

	req := &proto.TopicRequest{
		TopicName: topicName,
	}

	ctx, cancelFn := context.WithTimeout(c.getAuthContext(), common.GRPCCallTimeout)
	defer cancelFn()

	resp, err := c.pubSubClient.GetTopic(ctx, req, grpc.Trailer(&trailer))
	printTrailer(trailer)

	if err != nil {
		return nil, err
	}

	return resp, nil
}

// Wrapper function around the GetSchema RPC. This will add the OAuth credentials and make a call to fetch data about a specific schema
func (c *PubSubClient) GetSchema(schemaId string) (*proto.SchemaInfo, error) {
	var trailer metadata.MD

	req := &proto.SchemaRequest{
		SchemaId: schemaId,
	}

	ctx, cancelFn := context.WithTimeout(c.getAuthContext(), common.GRPCCallTimeout)
	defer cancelFn()

	resp, err := c.pubSubClient.GetSchema(ctx, req, grpc.Trailer(&trailer))
	printTrailer(trailer)

	if err != nil {
		return nil, err
	}

	return resp, nil
}

type SubscribeOpts struct {
	Channel chan<- map[string]any
	TopicName string
	ReplayPreset proto.ReplayPreset
	ReplayId []byte
	Cache cache.Cache
	ReplayIdKey string
}

// Wrapper function around the Subscribe RPC. This will add the OAuth credentials and create a separate streaming client that will be used to
// fetch data from the topic. This method will continuously consume messages unless an error occurs; if an error does occur then this method will
// return the last successfully consumed ReplayId as well as the error message. If no messages were successfully consumed then this method will return
// the same ReplayId that it originally received as a parameter
func (c *PubSubClient) Subscribe(subsOpts SubscribeOpts, db cache.Cache) ([]byte, error) {
	ctx, cancelFn := context.WithCancel(c.getAuthContext())
	defer cancelFn()

	// 60 is the maximum, if we don't get a response from Recv after 60 seconds, the connection is dead.
	// After 60 seconds, if the connection is alive, Recv will receive an empty response if there are no events in the queue.
	// Doc reference:
	// https://developer.salesforce.com/docs/platform/pub-sub-api/guide/flow-control.html#keeping-the-subscription-stream-alive-from-the-client
	timeoutDuration := 62*time.Second
	timeoutTimer := time.AfterFunc(timeoutDuration, func() {
		log.Warnf("Connection is dead, cancel it")
		cancelFn()
	})
	defer timeoutTimer.Stop()

	subscribeClient, err := c.pubSubClient.Subscribe(ctx)
	if err != nil {
		return subsOpts.ReplayId, err
	}
	defer subscribeClient.CloseSend()

	initialFetchRequest := &proto.FetchRequest{
		TopicName:    subsOpts.TopicName,
		ReplayPreset: subsOpts.ReplayPreset,
		NumRequested: common.Appetite,
	}
	if subsOpts.ReplayPreset == proto.ReplayPreset_CUSTOM && subsOpts.ReplayId != nil {
		initialFetchRequest.ReplayId = subsOpts.ReplayId
	}

	err = subscribeClient.Send(initialFetchRequest)
	// If the Send call returns an EOF error then print a log message but do not return immediately. Instead, let the Recv call (below) determine
	// if there's a more specific error that can be returned
	// See the SendMsg description at https://pkg.go.dev/google.golang.org/grpc#ClientStream
	if err == io.EOF {
		log.Debugf("WARNING - EOF error returned from initial Send call, proceeding anyway")
	} else if err != nil {
		return subsOpts.ReplayId, err
	}

	requestedEvents := initialFetchRequest.NumRequested

	// Store the Replay ID in the cache
	curReplayId := subsOpts.ReplayId
	err = subsOpts.Cache.SetCacheVal(subsOpts.ReplayIdKey, string(curReplayId))
	if err != nil {
		log.Debugf("Error updating ReplayId = %s", err)
	}

	for {
		log.Debugf("Waiting for events...")
		resp, err := subscribeClient.Recv()
		timeoutTimer.Reset(timeoutDuration)
		if err == io.EOF {
			log.Errorf("Recv IO EOF: %s", err)
			printTrailer(subscribeClient.Trailer())
			return curReplayId, fmt.Errorf("stream closed")
		} else if err != nil {
			log.Errorf("Recv error: %s", err)
			metadata := subscribeClient.Trailer()
			printTrailer(metadata)

			errorCode := metadata.Get("error-code")
			if len(errorCode) > 0 {
				if errorCode[0] == "sfdc.platform.eventbus.grpc.service.auth.error" {
					log.Warnf("Auth credentials outdated, relogin")
					c.Authenticate(db)
				}
			}

			return curReplayId, err
		}

		log.Debugf("Recv returned, check for events. Num events = %d", len(resp.Events))

		for _, event := range resp.Events {
			log.Debugf("Schema ID = %s", event.GetEvent().GetSchemaId())
			codec, err := c.fetchCodec(event.GetEvent().GetSchemaId())
			if err != nil {
				return curReplayId, err
			}

			parsed, _, err := codec.NativeFromBinary(event.GetEvent().GetPayload())
			if err != nil {
				return curReplayId, err
			}

			body, ok := parsed.(map[string]interface{})
			if !ok {
				return curReplayId, fmt.Errorf("error casting parsed event: %v", body)
			}

			// Store the Replay ID in the cache
			curReplayId = event.GetReplayId()
			err = subsOpts.Cache.SetCacheVal(subsOpts.ReplayIdKey, string(curReplayId))
			if err != nil {
				log.Debugf("Error updating ReplayId = %s", err)
			}

			//log.Debugf("event body: %+v\n", body)

			// Send event to channel
			subsOpts.Channel <- buildEvent(body, parseTypeName(codec))

			// decrement our counter to keep track of how many events have been requested but not yet processed. If we're below our configured
			// batch size then proactively request more events to stay ahead of the processor
			requestedEvents--
			if requestedEvents < common.Appetite {
				log.Debugf("Sending next FetchRequest...")
				fetchRequest := &proto.FetchRequest{
					TopicName:    subsOpts.TopicName,
					NumRequested: common.Appetite,
				}

				err = subscribeClient.Send(fetchRequest)
				// If the Send call returns an EOF error then print a log message but do not return immediately. Instead, let the Recv call (above) determine
				// if there's a more specific error that can be returned
				// See the SendMsg description at https://pkg.go.dev/google.golang.org/grpc#ClientStream
				if err == io.EOF {
					log.Debugf("WARNING - EOF error returned from subsequent Send call, proceeding anyway")
				} else if err != nil {
					return curReplayId, err
				}

				requestedEvents += fetchRequest.NumRequested
			}
		}
	}
}

// Unexported helper function to retrieve the cached codec from the PubSubClient's schema cache. If the schema ID is not found in the cache
// then a GetSchema call is made and the corresponding codec is cached for future use
func (c *PubSubClient) fetchCodec(schemaId string) (*goavro.Codec, error) {
	codec, ok := c.schemaCache[schemaId]
	if ok {
		log.Debugf("Fetched cached codec...")
		name := parseTypeName(codec)
		log.Debugf("Event type name = %s", name)
		return codec, nil
	}

	log.Debugf("Making GetSchema request for uncached schema...")
	schema, err := c.GetSchema(schemaId)
	if err != nil {
		return nil, err
	}

	log.Debugf("Creating codec from uncached schema...")
	codec, err = goavro.NewCodec(schema.GetSchemaJson())
	if err != nil {
		return nil, err
	}

	name := parseTypeName(codec)
	log.Debugf("Event type name = %s", name)

	c.schemaCache[schemaId] = codec

	return codec, nil
}

func parseTypeName(codec *goavro.Codec) string {
	var dat map[string]any
	byt := []byte(codec.CanonicalSchema())
	if err := json.Unmarshal(byt, &dat); err != nil {
		return ""
	}
	name, ok := dat["name"].(string)
	if ok {
		return name
	} else {
		return ""
	}
}

// Wrapper function around the Publish RPC. This will add the OAuth credentials and produce a single hardcoded event to the specified topic.
func (c *PubSubClient) Publish(topicName string, schema *proto.SchemaInfo) error {
	log.Debugf("Creating codec from schema...")
	codec, err := goavro.NewCodec(schema.SchemaJson)
	if err != nil {
		return err
	}

	sampleEvent := map[string]interface{}{
		"CreatedDate":        time.Now().Unix(),
		"CreatedById":        c.userID,
		"Mileage__c":         goavro.Union("double", 95443.0),
		"Cost__c":            goavro.Union("double", 99.40),
		"WorkDescription__c": goavro.Union("string", "Replaced front brakes"),
	}

	payload, err := codec.BinaryFromNative(nil, sampleEvent)
	if err != nil {
		return err
	}

	var trailer metadata.MD

	req := &proto.PublishRequest{
		TopicName: topicName,
		Events: []*proto.ProducerEvent{
			{
				SchemaId: schema.GetSchemaId(),
				Payload:  payload,
			},
		},
	}

	ctx, cancelFn := context.WithTimeout(c.getAuthContext(), common.GRPCCallTimeout)
	defer cancelFn()

	pubResp, err := c.pubSubClient.Publish(ctx, req, grpc.Trailer(&trailer))
	printTrailer(trailer)

	if err != nil {
		return err
	}

	result := pubResp.GetResults()
	if result == nil {
		return fmt.Errorf("nil result returned when publishing to %s", topicName)
	}

	if err := result[0].GetError(); err != nil {
		return fmt.Errorf(result[0].GetError().GetMsg())
	}

	return nil
}

// Wrapper function around the PublishStream RPC. This will add the OAuth credentials and produce an event to the topic every five seconds
func (c *PubSubClient) PublishStream(topicName string, schema *proto.SchemaInfo) error {
	log.Debugf("Creating codec from schema...")
	codec, err := goavro.NewCodec(schema.SchemaJson)
	if err != nil {
		return err
	}

	ctx, cancelFn := context.WithCancel(c.getAuthContext())
	defer cancelFn()

	publishClient, err := c.pubSubClient.PublishStream(ctx)
	if err != nil {
		return err
	}

	sampleEvent := map[string]interface{}{
		"CreatedDate":        time.Now().Unix(),
		"CreatedById":        c.userID,
		"Mileage__c":         goavro.Union("double", 95443.0),
		"Cost__c":            goavro.Union("double", 99.40),
		"WorkDescription__c": goavro.Union("string", "Replaced front brakes"),
	}

	payload, err := codec.BinaryFromNative(nil, sampleEvent)
	if err != nil {
		return err
	}

	publishRequest := &proto.PublishRequest{
		TopicName: topicName,
		Events: []*proto.ProducerEvent{
			{
				SchemaId: schema.GetSchemaId(),
				Payload:  payload,
			},
		},
	}

	err = publishClient.Send(publishRequest)
	// If the Send call returns an EOF error then print a log message but do not return immediately. Instead, let the Recv call (below) determine
	// if there's a more specific error that can be returned
	// See the SendMsg description at https://pkg.go.dev/google.golang.org/grpc#ClientStream
	if err == io.EOF {
		log.Debugf("WARNING - EOF error returned from initial Send call, proceeding anyway")
	} else if err != nil {
		return err
	}

	log.Debugf("Entering event loop...")

	var resErrMutex sync.Mutex
	var resErr error

	shutdownGoroutine := func(err error) {
		cancelFn()

		resErrMutex.Lock()
		defer resErrMutex.Unlock()

		// only capture the first error returned
		if resErr == nil {
			resErr = err
		}
	}

	wg := sync.WaitGroup{}
	wg.Add(2)

	// sender goroutine. This goroutine will attempt to publish a new event every 5 seconds. This goroutine will run until one of the following
	// conditions is met:
	// 1. the receiver goroutine returned an error and exited
	// 2. this goroutine encounters an error while publishing
	go func() {
		defer wg.Done()
		defer publishClient.CloseSend()

		for {
			select {
			case <-ctx.Done():
				return
			default:
				time.Sleep(5 * time.Second)

				log.Debugf("Sending next PublishRequest...")
				sampleEvent["CreatedDate"] = time.Now().Unix()

				payload, sendErr := codec.BinaryFromNative(nil, sampleEvent)
				if sendErr != nil {
					shutdownGoroutine(sendErr)
					return
				}

				publishRequest := &proto.PublishRequest{
					TopicName: topicName,
					Events: []*proto.ProducerEvent{
						{
							SchemaId: schema.GetSchemaId(),
							Payload:  payload,
						},
					},
				}

				sendErr = publishClient.Send(publishRequest)
				// if we encounter an EOF error from the Send method then exit this goroutine without canceling the context or recording the error.
				// The Recv method called in the receiver goroutine may return a more specific error explaining why the stream was closed.
				// See the SendMsg description at https://pkg.go.dev/google.golang.org/grpc#ClientStream
				if sendErr == io.EOF {
					log.Debugf("WARNING - EOF error returned from subsequent Send call, proceeding anyway")
					return
				} else if sendErr != nil {
					shutdownGoroutine(sendErr)
					return
				}
			}
		}
	}()

	// receiver goroutine. This goroutine will attempt to receive the PublishStream responses as they are sent back from the Pub/Sub API. This
	// goroutine will run until one of the following conditions is met:
	// 1. the sender goroutine returned an error and exited
	// 2. this goroutine either encounters an error while receiving or the PublishStream response indicates an error occurred while publishing
	go func() {
		defer wg.Done()

		for {
			select {
			case <-ctx.Done():
				return
			default:
				pubResp, recvErr := publishClient.Recv()
				if recvErr == io.EOF {
					printTrailer(publishClient.Trailer())
					shutdownGoroutine(fmt.Errorf("stream closed"))
					return
				} else if recvErr != nil {
					printTrailer(publishClient.Trailer())
					shutdownGoroutine(recvErr)
					return
				}

				results := pubResp.GetResults()
				if results == nil {
					shutdownGoroutine(fmt.Errorf("nil results received"))
					return
				}

				for _, res := range results {
					if res.GetError() != nil {
						shutdownGoroutine(fmt.Errorf(res.GetError().GetMsg()))
						return
					}
				}

				log.Debugf("successfully published event")
			}
		}
	}()

	wg.Wait()

	return resErr
}

// Returns a new context with the necessary authentication parameters for the gRPC server
func (c *PubSubClient) getAuthContext() context.Context {
	return metadata.NewOutgoingContext(context.Background(), metadata.Pairs(
		tokenHeader, c.accessToken,
		instanceHeader, c.instanceURL,
		tenantHeader, c.orgID,
	))
}

// Creates a new connection to the gRPC server and returns the wrapper struct
func NewGRPCClient() (*PubSubClient, error) {
	dialOpts := []grpc.DialOption{
		grpc.WithBlock(),
	}

	if common.GRPCEndpoint == "localhost:7011" {
		dialOpts = append(dialOpts, grpc.WithTransportCredentials(insecure.NewCredentials()))
	} else {
		certs := getCerts()
		creds := credentials.NewClientTLSFromCert(certs, "")
		dialOpts = append(dialOpts, grpc.WithTransportCredentials(creds))
	}

	ctx, cancelFn := context.WithTimeout(context.Background(), common.GRPCDialTimeout)
	defer cancelFn()

	conn, err := grpc.DialContext(ctx, common.GRPCEndpoint, dialOpts...)
	if err != nil {
		return nil, err
	}

	return &PubSubClient{
		conn:         conn,
		pubSubClient: proto.NewPubSubClient(conn),
		schemaCache:  make(map[string]*goavro.Codec),
	}, nil
}

// Fetches system certs and returns them if possible. If unable to fetch system certs then an empty cert pool is returned instead
func getCerts() *x509.CertPool {
	if certs, err := x509.SystemCertPool(); err == nil {
		return certs
	}

	return x509.NewCertPool()
}

// Helper function to display trailers on the console in a more readable format
func printTrailer(trailer metadata.MD) {
	if len(trailer) == 0 {
		log.Debugf("no trailers returned")
		return
	}

	log.Debugf("beginning of trailers")
	for key, val := range trailer {
		log.Debugf("[trailer] = %s, [value] = %s", key, val)
	}
	log.Debugf("end of trailers")
}

func transformEvent(ev map[string]any) map[string]any {
	nrEv := map[string]any{}

	for evName, evValue := range ev {
		if evName == "CreatedDate" || evName == "CreatedById" {
			nrEv[evName] = evValue
		} else {
			attrType := "other"
			if val, ok := evValue.(map[string]any); ok {
				if _, is_string := val["string"]; is_string {
					attrType = "string"
				} else if _, is_long := val["long"]; is_long {
					attrType = "long"
				} else if _, is_int := val["int"]; is_int {
					attrType = "int"
				} else if _, is_double := val["double"]; is_double {
					attrType = "double"
				}

				nrEv[evName] = val[attrType]
			}
		}
	}

	return nrEv
}

func buildEvent(body map[string]any, topicName string) map[string]any {
	ev := transformEvent(body)
	topicNameComponents := strings.Split(topicName, ".")
	eventType := "SFDCEvent"
	if len(topicNameComponents) > 0 {
		eventType = topicNameComponents[len(topicNameComponents)-1]
	}
	ev["eventType"] = "SFDC" + eventType

	return ev
}
