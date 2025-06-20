package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"sync"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/grpcclient"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/proto"
	"github.com/sirupsen/logrus"

	labslog "github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
)

var integrationConf stream.Config

func main() {
	if os.Getenv("LOGS") == "1" {
		labslog.RootLogger.SetLevel(logrus.TraceLevel)
	}

	var err error
	integrationConf, err = stream.ReadConfig("config.yml") ; if err != nil {
		log.Fatalln("Error loading config = ", err)
	}

	fmt.Printf("Config = %+v\n", integrationConf)

	stream.FillSalesforceCredentials(integrationConf)

	ctx := context.Background()

	i, err := stream.NewStreamIntegration(ctx) ; if err != nil {
		log.Fatalln("Error creating NR integration = ", err)
	}

	exporter := stream.NewExporter(i)

	ch := make(chan map[string]any)

	streamComponent := stream.NewStreamComponent(exporter, ch)
	i.AddComponent(&streamComponent)

	go readEventStreams(ch, integrationConf.EventStream.Topics)

	// Run the integration
	defer i.Shutdown(ctx)
	err = i.Run(ctx) ; if err != nil {
		log.Fatalln("Error running the integration = ", err)
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
	db := stream.BuildCache(integrationConf)

	log.Printf("Creating gRPC client...")
	client, err := grpcclient.NewGRPCClient()
	if err != nil {
		log.Fatalf("could not create gRPC client: %v", err)
	}
	defer client.Close()

	log.Printf("Populating auth token...")
	err = client.Authenticate()
	if err != nil {
		client.Close()
		log.Fatalf("could not authenticate: %v", err)
	}

	log.Printf("Populating user info...")
	err = client.FetchUserInfo()
	if err != nil {
		client.Close()
		log.Fatalf("could not fetch user info: %v", err)
	}

	replayIdKey := topicName + "_last_replay_id"

	var curReplayId []byte = nil
	
	// Try to get replay ID from the cache
	res, err := db.GetCacheVal(replayIdKey) ; if err != nil {
		labslog.Debugf("Error reading '%s' from cache: %s", replayIdKey, err.Error())
	}

	if res != nil {
		res, ok := res.(string)
		if ok {
			curReplayId = []byte(res)
			labslog.Infof("Got Replay ID from cache")
		} else {
			labslog.Debugf("Error reading '%s' as a string from cache", replayIdKey)
		}
	}

	for {
		log.Printf("Subscribing to topic %s", topicName)

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
			log.Printf("error occurred while subscribing to topic: %v", err)
		}
	}
}
