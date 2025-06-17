package main

import (
	"context"
	"errors"
	"log"
	"os"
	"sync"
	"time"

	"github.com/newrelic/newrelic-salesforce-exporter/pkg/cache/redis"
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
	INTEGRATION_ID   = "com.newrelic.salesforce.eventstream"
	INTEGRATION_NAME = "New Relic Salesforce Event Streaming"
	MAX_BUFFER_SIZE  = 10
)

type StreamComponent struct {
	exporter pipeline.EventsExporter
	ch chan map[string]any
	buffer []model.Event
}

func NewStreamComponent(exporter pipeline.EventsExporter, ch chan map[string]any) StreamComponent {
	return StreamComponent {
		exporter: exporter,
		ch: ch,
		buffer: make([]model.Event, 0),
	}
}

func (c *StreamComponent)GetId() string {
	return "sfdc-stream-component"
}

func (c *StreamComponent)ExecuteSync(ctx context.Context) error {
	labslog.Debugf("-------> StreamComponent ExecuteSync")
	for {
		select {
		case <-ctx.Done():
			labslog.Debugf("Done.")
			return nil
		case ev := <-c.ch:
			labslog.Debugf("Received an event from the stream")

			eventType := ev["eventType"].(string)
			delete(ev, "eventType")

			var timestamp time.Time
			if ev["EventDate"] != nil {
				timestamp = time.UnixMilli(ev["EventDate"].(int64))
				delete(ev, "EventDate")
			} else {
				timestamp = time.Now()
			}

			event := model.NewEvent(eventType, ev, timestamp)
			c.buffer = append(c.buffer, event)

			labslog.Debugf("Event buffered")

			if len(c.buffer) >= MAX_BUFFER_SIZE {
				labslog.Debugf("-----> Harvest events!")
				err := c.exporter.ExportEvents(ctx, c.buffer)
				if err != nil {
					labslog.Debugf("Event export failed: %s", err.Error())
				}
				c.buffer = make([]model.Event, 0)
			}

			break
		}
	}
}

func (c *StreamComponent)Start(ctx context.Context, wg *sync.WaitGroup) error {
	return errors.New("StreamComponent should never use Start")
}

func (c *StreamComponent)Execute(ctx context.Context) error {
	return errors.New("StreamComponent should never use Execute")
}

func (c *StreamComponent)Shutdown(ctx context.Context) error {
	return errors.New("StreamComponent should never use Shitdown")
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

func WithRunAsService(runAsService bool) integration.LabsIntegrationOpt {
	return func(li *integration.LabsIntegration) error {
		li.RunAsService = runAsService
		return nil
	}
}

func NewStreamIntegration(name, id, appName string, ctx context.Context,
	labsIntegrationOpts ...integration.LabsIntegrationOpt,
) (*integration.LabsIntegration, error) {
	i, err := integration.NewStandaloneIntegration(
		INTEGRATION_NAME,
		INTEGRATION_ID,
		INTEGRATION_NAME,
		integration.WithLicenseKey(),
		integration.WithApiKey(),
		integration.WithAccountId(),
		integration.WithEvents(ctx),
		integration.WithLogs(ctx),
		WithRunAsService(false),
	)
	return i, err
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

	i, err := NewStreamIntegration(
		INTEGRATION_NAME,
		INTEGRATION_ID,
		INTEGRATION_NAME,
		ctx,
	)

	if err != nil {
		log.Fatalln("Error creating NR integration = ", err)
	}

	newRelicExporter := exporters.NewNewRelicExporter(
		//TODO: set integration data
		"newrelic",
		"integration_name",
		"integration_id",
		i.NrClient,
		i.GetLicenseKey(),
		i.GetRegion(),
		i.DryRun,
	)

	ch := make(chan map[string]any)

	streamComponent := NewStreamComponent(newRelicExporter, ch)
	i.AddComponent(&streamComponent)

	go readEventStreams(ch)

	// Run the integration
	defer i.Shutdown(ctx)
	err = i.Run(ctx)

	if err != nil {
		log.Fatalln("Error running the integration = ", err)
	}
}

func readEventStreams(ch chan<- map[string]any) {
	// Create one subscriber per topic
	var wg sync.WaitGroup
	for _, topicName := range common.Topics {
		wg.Add(1)
		go func(topicName string) {
			defer wg.Done()
			subscribeToTopic(topicName, ch)
		}(topicName)
	}
	wg.Wait()
}

func subscribeToTopic(topicName string, ch chan<- map[string]any) {
	//TODO: read config from file
	db := redis.NewRedisCache(redis.RedisConfig{
		Host: "localhost",
		Port: 6379,
		DbNumber: 0,
		Password: "",
		ExpireDays: 1,
	})

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

	replayIdKey := topicName + "_last_replay_id"

	curReplayId := common.ReplayId
	
	//TODO: get curReplayId from cache

	// err = db.SetCacheVal(replayIdKey, string(curReplayId))
	// if err != nil {
	// 	labslog.Debugf("Error updating ReplayId = %s", err)
	// }

	for {
		log.Printf("Subscribing to topic %s", topicName)

		replayPreset := common.ReplayPreset
		if curReplayId != nil {
			replayPreset = proto.ReplayPreset_CUSTOM
		}

		curReplayId, err = client.Subscribe(ch, topicName, replayPreset, curReplayId, &db, replayIdKey)
		if err != nil {
			log.Printf("error occurred while subscribing to topic: %v", err)
		}
	}
}

// TODO: explore how viper loads config from env variables
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
