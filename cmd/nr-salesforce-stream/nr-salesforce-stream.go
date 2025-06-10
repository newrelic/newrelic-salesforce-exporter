package main

import (
	"log"
	"sync"

	"github.com/newrelic/newrelic-salesforce-exporter/pkg/pubsub/common"
	"github.com/newrelic/newrelic-salesforce-exporter/pkg/pubsub/grpcclient"
	"github.com/newrelic/newrelic-salesforce-exporter/pkg/pubsub/proto"
	"github.com/spf13/viper"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration"
)

// TODO: use the labs SDK to
// - Send events or logs to to NR

type Config struct {
	Version     string `mapstructure:"version"`
	IsTemplate  bool   `mapstructure:"is_template"` //TODO: optional, default value False
	EventStream struct {
		IntegrationName string `mapstructure:"integration_name"`
		Auth            struct {
			TokenUrl string `mapstructure:"token_url"`
			UserPass struct {
				ClientId     string `mapstructure:"client_id"`
				ClientSecret string `mapstructure:"client_secret"`
				Username     string `mapstructure:"username"`
				Password     string `mapstructure:"password"`
			} `mapstructure:"user_pass"`
		} `mapstructure:"auth"`
	} `mapstructure:"event_stream"`
}

func main() {
	conf, err := readConfig("config.yml")
	if err != nil {
		log.Fatalln("Error loading config = ", err)
	}

	common.GrantType = "password"
	common.ClientId = conf.EventStream.Auth.UserPass.ClientId
	common.ClientSecret = conf.EventStream.Auth.UserPass.ClientSecret
	common.Username = conf.EventStream.Auth.UserPass.Username
	common.Password = conf.EventStream.Auth.UserPass.Password
	common.OAuthEndpoint = conf.EventStream.Auth.TokenUrl

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

func readConfig(file string) (Config, error) {
	if err := integration.NewConfigWithFile(file); err != nil {
		return Config{}, err
	}

	conf := Config{}

	if err := viper.Unmarshal(&conf); err != nil {
		return Config{}, err
	}

	//TODO: check conf integrity

	return conf, nil
}
