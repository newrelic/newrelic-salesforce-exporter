package main

import (
	"context"
	"os"
	"sync"

	"github.com/newrelic/newrelic-salesforce-exporter/internal"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/grpcclient"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/proto"
	"github.com/sirupsen/logrus"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
)

var integrationConf internal.Config

func main() {
	loglevel := os.Getenv("LOGS")
	switch loglevel {
	case "0":
		log.RootLogger.SetLevel(logrus.TraceLevel)
	case "1":
		log.RootLogger.SetLevel(logrus.DebugLevel)
	case "2":
		log.RootLogger.SetLevel(logrus.InfoLevel)
	case "3":
		log.RootLogger.SetLevel(logrus.WarnLevel)
	case "4":
		log.RootLogger.SetLevel(logrus.ErrorLevel)
	}
	
	var err error
	integrationConf, err = internal.ReadConfig("config.yml") ; if err != nil {
		log.Errorf("Error loading config = %s", err)
		os.Exit(1)
	}

	// log.Debugf("Config = %+v", integrationConf)

	stream.FillSalesforceCredentials(integrationConf)

	ctx := context.Background()

	i, err := stream.NewStreamIntegration(ctx) ; if err != nil {
		log.Errorf("Error creating NR integration = %s", err)
		os.Exit(1)
	}

	exporter := stream.NewExporter(i)

	ch := make(chan map[string]any)

	streamComponent := stream.NewStreamComponent(exporter, ch)
	i.AddComponent(&streamComponent)

	go readEventStreams(ch, integrationConf.EventStream.Topics)

	// Run the integration
	defer i.Shutdown(ctx)
	err = i.Run(ctx) ; if err != nil {
		log.Errorf("Error running the integration = %s", err)
		os.Exit(1)
	}
}

func readEventStreams(ch chan<- map[string]any, topics []string) {
	// Create one subscriber per topic
	var wg sync.WaitGroup
	for _, topicName := range topics {
		wg.Add(1)
		go func(topicName string) {
			defer wg.Done()
			subscribeToTopic(topicName, ch)
		}(topicName)
	}
	wg.Wait()
}

func subscribeToTopic(topicName string, ch chan<- map[string]any) {
	db := cache.BuildCache(integrationConf.EventStream.Cache)

	log.Debugf("Creating gRPC client...")
	client, err := grpcclient.NewGRPCClient()
	if err != nil {
		log.Errorf("could not create gRPC client: %s", err)
		os.Exit(1)
	}
	defer client.Close()

	log.Debugf("Populating auth token...")
	err = client.Authenticate()
	if err != nil {
		client.Close()
		log.Errorf("could not authenticate: %s", err)
		os.Exit(1)
	}

	log.Debugf("Populating user info...")
	err = client.FetchUserInfo()
	if err != nil {
		client.Close()
		log.Errorf("could not fetch user info: %s", err)
		os.Exit(1)
	}

	replayIdKey := topicName + "_last_replay_id"

	var curReplayId []byte = nil
	
	// Try to get replay ID from the cache
	res, err := db.GetCacheVal(replayIdKey) ; if err != nil {
		log.Debugf("Error reading '%s' from cache: %s", replayIdKey, err.Error())
	}

	if res != nil {
		res, ok := res.(string)
		if ok {
			curReplayId = []byte(res)
			log.Debugf("Got Replay ID from cache")
		} else {
			log.Debugf("Error reading '%s' as a string from cache", replayIdKey)
		}
	}

	for {
		log.Debugf("Subscribing to topic %s", topicName)

		replayPreset := proto.ReplayPreset_LATEST
		if curReplayId != nil {
			replayPreset = proto.ReplayPreset_CUSTOM
		}

		subsOpts := grpcclient.SubscribeOpts {
			Channel: ch,
			TopicName: topicName,
			ReplayPreset: replayPreset,
			ReplayId: curReplayId,
			Cache: db,
			ReplayIdKey: replayIdKey,
		}

		curReplayId, err = client.Subscribe(subsOpts)
		if err != nil {
			log.Errorf("error occurred while subscribing to topic: %s", err)
		}
	}
}
