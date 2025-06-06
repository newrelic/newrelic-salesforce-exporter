package main

import (
	"encoding/json"
	"log"
	"os"
	"sync"

	"github.com/newrelic/newrelic-salesforce-exporter/pkg/common"
	"github.com/newrelic/newrelic-salesforce-exporter/pkg/grpcclient"
	"github.com/newrelic/newrelic-salesforce-exporter/pkg/proto"
)

func main() {
	var credentials map[string]string
	file_content, err := os.ReadFile("credentials.json")
	file_content = []byte(file_content)
	if err := json.Unmarshal(file_content, &credentials); err != nil {
		log.Fatalf("could not read file credentials.json")
	}
	common.GrantType = credentials["GrantType"]
	common.ClientId = credentials["ClientId"]
	common.ClientSecret = credentials["ClientSecret"]
	common.Username = credentials["Username"]
	common.Password = credentials["Password"]
	common.OAuthEndpoint = credentials["OAuthEndpoint"]

	if common.ReplayPreset == proto.ReplayPreset_CUSTOM && common.ReplayId == nil {
		log.Fatalf("the replayId variable must be populated when the replayPreset variable is set to CUSTOM")
	} else if common.ReplayPreset != proto.ReplayPreset_CUSTOM && common.ReplayId != nil {
		log.Fatalf("the replayId variable must not be populated when the replayPreset variable is set to EARLIEST or LATEST")
	}

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

	for _, topicName := range common.Topics {
		log.Printf("Making GetTopic request...")
		topic, err := client.GetTopic(topicName)
		if err != nil {
			client.Close()
			log.Fatalf("could not fetch topic: %v", err)
		}

		if !topic.GetCanSubscribe() {
			client.Close()
			log.Fatalf("this user is not allowed to subscribe to the following topic: %s", topicName)
		}
	}

	var wg sync.WaitGroup
	for _, topicName := range common.Topics {
		wg.Add(1)
		go func(topicName string) {
			defer wg.Done()
			subscribe(client, topicName)
		}(topicName)
	}
	wg.Wait()
}

func subscribe(client *grpcclient.PubSubClient, topicName string) {
	var err error
	curReplayId := common.ReplayId
	for {
		log.Printf("Subscribing to topic %s", topicName)

		replayPreset := common.ReplayPreset
		if curReplayId != nil {
			replayPreset = proto.ReplayPreset_CUSTOM
		}

		curReplayId, err = client.Subscribe(topicName, replayPreset, curReplayId)
		if err != nil {
			log.Printf("error occurred while subscribing to topic: %v", err)
		}
	}
}
