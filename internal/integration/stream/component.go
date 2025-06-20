package stream

import (
	"context"
	"errors"
	"sync"
	"time"

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

func WithRunAsService(runAsService bool) integration.LabsIntegrationOpt {
	return func(li *integration.LabsIntegration) error {
		li.RunAsService = runAsService
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
		integration.WithApiKey(),
		integration.WithAccountId(),
		integration.WithEvents(ctx),
		integration.WithLogs(ctx),
		WithRunAsService(false),
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