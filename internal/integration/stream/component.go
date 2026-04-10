package stream

import (
	"context"
	"errors"
	"sync"
	"time"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/exporters"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/model"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/pipeline"
)

const (
	INTEGRATION_ID   = "com.newrelic.salesforce.eventstream"
	INTEGRATION_NAME = "New Relic Salesforce Event Streaming"
	MAX_BUFFER_SIZE  = 10
)

type EventLogExporter interface {
	pipeline.EventsExporter
	pipeline.LogsExporter
}

type DataFormat int

const (
	Events DataFormat = iota
	Logs
)

type StreamComponent struct {
	exporter      EventLogExporter
	ch            chan map[string]any
	eventBuff     []model.Event
	logBuff       []model.Log
	format        DataFormat
	maxBufferSize int
	instanceName  string
}

func NewStreamComponent(exporter EventLogExporter, ch chan map[string]any, formatConf string, instanceName string) (StreamComponent, error) {
	var format DataFormat
	var eventBuff []model.Event = nil
	var logBuff []model.Log = nil

	switch formatConf {
	case "events":
		format = Events
		eventBuff = make([]model.Event, 0)
	case "logs":
		format = Logs
		logBuff = make([]model.Log, 0)
	default:
		err := errors.New("Format must be either 'events' or 'logs'")
		return StreamComponent{}, err
	}

	return StreamComponent{
		exporter:      exporter,
		ch:            ch,
		eventBuff:     eventBuff,
		logBuff:       logBuff,
		format:        format,
		maxBufferSize: MAX_BUFFER_SIZE,
		instanceName:  instanceName,
	}, nil
}

func (c *StreamComponent) GetId() string {
	return "sfdc-stream-component"
}

func (c *StreamComponent) ExecuteSync(ctx context.Context) error {
	log.Debugf("StreamComponent ExecuteSync")
	for {
		select {
		case <-ctx.Done():
			log.Debugf("Done.")
			return nil
		case ev := <-c.ch:
			log.Debugf("Received an event from the stream")

			eventType := ev["eventType"].(string)
			delete(ev, "eventType")

			var timestamp time.Time
			if ev["EventDate"] != nil {
				timestamp = time.UnixMilli(ev["EventDate"].(int64))
				delete(ev, "EventDate")
			} else {
				log.Warnf("Event '%s' has no 'EventDate'. Using current time.", eventType)
				timestamp = time.Now()
			}

			ev["sf.instance.name"] = c.instanceName

			switch c.format {
			case Events:
				event := model.NewEvent(eventType, ev, timestamp)
				c.eventBuff = append(c.eventBuff, event)

				log.Debugf("Event buffered")

				if len(c.eventBuff) >= c.maxBufferSize {
					log.Debugf("Harvest events!")
					err := c.exporter.ExportEvents(ctx, c.eventBuff)
					if err != nil {
						log.Debugf("Event export failed: %s", err.Error())
					}
					c.eventBuff = make([]model.Event, 0)
				}
			case Logs:
				mlog := model.NewLog(eventType, ev, timestamp)
				c.logBuff = append(c.logBuff, mlog)

				log.Debugf("Log buffered")

				if len(c.logBuff) >= c.maxBufferSize {
					log.Debugf("Harvest logs!")
					err := c.exporter.ExportLogs(ctx, c.logBuff)
					if err != nil {
						log.Debugf("Log export failed: %s", err.Error())
					}
					c.logBuff = make([]model.Log, 0)
				}
			}
		}
	}
}

func (c *StreamComponent) Start(ctx context.Context, wg *sync.WaitGroup) error {
	return errors.New("StreamComponent should never use Start")
}

func (c *StreamComponent) Execute(ctx context.Context) error {
	return errors.New("StreamComponent should never use Execute")
}

func (c *StreamComponent) Shutdown(ctx context.Context) error {
	return errors.New("StreamComponent should never use Shitdown")
}

func withRunAsService(runAsService bool) integration.LabsIntegrationOpt {
	return func(li *integration.LabsIntegration) error {
		li.RunAsService = runAsService
		return nil
	}
}

func withOptionalApiKey() integration.LabsIntegrationOpt {
	return func(li *integration.LabsIntegration) error {
		err := (integration.WithApiKey())(li)
		if err != nil {
			log.Debugf("ApiKey not set, ignoring")
		}
		return nil
	}
}

func NewStreamIntegration(ctx context.Context,
	labsIntegrationOpts ...integration.LabsIntegrationOpt,
) (*integration.LabsIntegration, error) {
	i, err := integration.NewStandaloneIntegration(
		INTEGRATION_NAME,
		INTEGRATION_ID,
		INTEGRATION_NAME,
		integration.WithLicenseKey(),
		withOptionalApiKey(),
		integration.WithAccountId(),
		integration.WithEvents(ctx),
		integration.WithLogs(ctx),
		withRunAsService(false),
	)
	return i, err
}

func NewExporter(i *integration.LabsIntegration) *exporters.NewRelicExporter {
	return exporters.NewNewRelicExporter(
		INTEGRATION_ID,
		INTEGRATION_NAME,
		INTEGRATION_ID,
		i.NrClient,
		i.GetLicenseKey(),
		i.GetRegion(),
		i.DryRun,
	)
}
