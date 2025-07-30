package main

import (
	"context"
	"os"
	"sync"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/common"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/grpcclient"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/stream/pubsub/proto"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
)

var integrationConf config.Config

func main() {
	ctx := context.Background()

	i, err := stream.NewStreamIntegration(ctx)
	if err != nil {
		log.Errorf("Error creating NR integration = %s", err)
		os.Exit(1)
	}
	
	integrationConf, err = config.ReadConfig()
	if err != nil {
		log.Errorf("Error loading config = %s", err)
		os.Exit(1)
	}

	if err := stream.IntegrityCheck(integrationConf); err != nil {
		log.Errorf("Error checking config integrity = %s", err)
		os.Exit(1)
	}

	common.FillCredentials(integrationConf.EventStream.Auth)

	exporter := stream.NewExporter(i)

	ch := make(chan map[string]any)

	streamComponent, err := stream.NewStreamComponent(exporter, ch, integrationConf.Format)
	if err != nil {
		log.Errorf("Error creating stream component = %s", err)
		os.Exit(1)
	}
	i.AddComponent(&streamComponent)

	go readEventStreams(ch, integrationConf.EventStream.Topics)

	// Run the integration
	defer i.Shutdown(ctx)
	err = i.Run(ctx)
	if err != nil {
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

	curReplayId := readReplayIdFromCache(db, replayIdKey)

	for {
		log.Debugf("Subscribing to topic %s", topicName)

		replayPreset := proto.ReplayPreset_LATEST
		if curReplayId != nil {
			replayPreset = proto.ReplayPreset_CUSTOM
		}

		subsOpts := grpcclient.SubscribeOpts{
			Channel:      ch,
			TopicName:    topicName,
			ReplayPreset: replayPreset,
			ReplayId:     curReplayId,
			Cache:        db,
			ReplayIdKey:  replayIdKey,
		}

		curReplayId, err = client.Subscribe(subsOpts)
		if err != nil {
			log.Errorf("error occurred while subscribing to topic: %s", err)
		}
	}
}

func readReplayIdFromCache(db cache.Cache, replayIdKey string) []byte {
	var curReplayId []byte = nil

	// Try to get replay ID from the cache
	cacheResp, err := db.GetCacheVal(replayIdKey)
	if err != nil {
		log.Errorf("Error reading '%s' from cache: %s", replayIdKey, err.Error())
	}

	if cacheResp != nil {
		cacheResp, ok := cacheResp.(string)
		if ok {
			if cacheResp != "" {
				curReplayId = []byte(cacheResp)
				log.Debugf("Got Replay ID from cache")
			} else {
				log.Debugf("Read '%s' from cache and is empty, ignoring.", replayIdKey)
			}
		} else {
			log.Errorf("Error reading '%s' as a string from cache", replayIdKey)
		}
	}

	return curReplayId
}
