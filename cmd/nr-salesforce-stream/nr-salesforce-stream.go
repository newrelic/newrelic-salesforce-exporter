package main

import (
	"context"
	"log"
	"os"
	"sync"
	"time"

	"github.com/newrelic/newrelic-salesforce-exporter/pkg/pubsub/common"
	"github.com/newrelic/newrelic-salesforce-exporter/pkg/pubsub/grpcclient"
	"github.com/newrelic/newrelic-salesforce-exporter/pkg/pubsub/proto"
	"github.com/sirupsen/logrus"
	"github.com/spf13/viper"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/exporters"
	labslog "github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/model"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/pipeline"
)

const (
	INTEGRATION_ID   = "com.newrelic.salesforce.event.stream"
	INTEGRATION_NAME = "New Relic Salesforce Event Streaming"
)

type eventStreamReceiver struct {
	ch <-chan map[string]any
}

func (t *eventStreamReceiver) GetId() string {
	return "sfdc-event-stream-receiver"
}

func (t *eventStreamReceiver) PollEvents(ctx context.Context, writer chan<- model.Event) error {
	for {
		ev := <-t.ch
		labslog.Debugf("Send new event.")
		writer <- model.NewEvent("SFDCEvent", ev, time.Now())
	}
}

type Config struct {
	Version    string `mapstructure:"version"`
	IsTemplate bool   `mapstructure:"is_template"` //TODO: optional, default value False

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
	if os.Getenv("LOGS") == "1" {
		labslog.RootLogger.SetLevel(logrus.TraceLevel)
	}

	conf, err := readConfig("config.yml")
	if err != nil {
		log.Fatalln("Error loading config = ", err)
	}

	fillSalesforceCredentials(conf)

	ctx := context.Background()
	i, err := integration.NewStandaloneIntegration(
		INTEGRATION_NAME,
		INTEGRATION_ID,
		INTEGRATION_NAME,
		integration.WithLicenseKey(),
		integration.WithApiKey(),
		integration.WithAccountId(),
		integration.WithEvents(ctx),
		integration.WithLogs(ctx),
	)

	if err != nil {
		log.Fatalln("Error creating NR integration = ", err)
	}

	newRelicExporter := exporters.NewNewRelicExporter(
		"newrelic",
		"integration_name",
		"integration_id",
		i.NrClient,
		i.GetLicenseKey(),
		i.GetRegion(),
		i.DryRun,
	)

	pipe := pipeline.NewEventsPipeline("sfdc-event-stream-pipeline")
	ch := make(chan map[string]any)

	pipe.AddReceiver(&eventStreamReceiver{ch})
	pipe.AddExporter(newRelicExporter)
	i.AddComponent(pipe)

	go readEventStream(ch)

	// Run the integration
	defer i.Shutdown(ctx)
	err = i.Run(ctx)

	if err != nil {
		log.Fatalln("Error running the integration = ", err)
	}
}

func readEventStream(ch chan<- map[string]any) {
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

	// Create one subscriber per topic
	var wg sync.WaitGroup
	for _, topicName := range common.Topics {
		wg.Add(1)
		go func(topicName string) {
			defer wg.Done()
			subscribe(ch, client, topicName)
		}(topicName)
	}
	wg.Wait()
}

func subscribe(ch chan<- map[string]any, client *grpcclient.PubSubClient, topicName string) {
	var err error
	curReplayId := common.ReplayId
	for {
		log.Printf("Subscribing to topic %s", topicName)

		replayPreset := common.ReplayPreset
		if curReplayId != nil {
			replayPreset = proto.ReplayPreset_CUSTOM
		}

		curReplayId, err = client.Subscribe(ch, topicName, replayPreset, curReplayId)
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

func fillSalesforceCredentials(conf Config) {
	common.GrantType = "password"
	common.ClientId = conf.EventStream.Auth.UserPass.ClientId
	common.ClientSecret = conf.EventStream.Auth.UserPass.ClientSecret
	common.Username = conf.EventStream.Auth.UserPass.Username
	common.Password = conf.EventStream.Auth.UserPass.Password
	common.OAuthEndpoint = conf.EventStream.Auth.TokenUrl
}
