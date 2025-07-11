package main

import (
	"context"
	"fmt"
	"os"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/exporters"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/model"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/pipeline"
)

const (
	INTEGRATION_ID   = "com.newrelic.salesforce.eventlog"
	INTEGRATION_NAME = "New Relic Salesforce Event Log"
	DEFAULT_INTERVAL = 5
)

type SalesforceEventsReceiver struct {
	i *integration.LabsIntegration
}

func (s *SalesforceEventsReceiver) GetId() string {
	return "salesforce-events-receiver"
}

func (s *SalesforceEventsReceiver) PollEvents(context context.Context, writer chan <- model.Event) error {
	//TODO: send events
	fmt.Printf("-----> Polling events")
	return nil	
}

func NewSalesforceEventsReceiver(i *integration.LabsIntegration) (pipeline.EventsReceiver, error) {
	return &SalesforceEventsReceiver{
		i: i,
	}, nil
}

func main() {
	ctx := context.Background()

	// Create the integration with options
	i, err := integration.NewStandaloneIntegration(
		INTEGRATION_NAME,
		INTEGRATION_ID,
		INTEGRATION_NAME,
		integration.WithInterval(DEFAULT_INTERVAL),
		integration.WithLicenseKey(),
		integration.WithEvents(ctx),
		integration.WithLastUpdate(),
		integration.WithLogs(ctx),
	)

	if err != nil {
		log.Errorf("Error creating NR integration = %s", err)
		os.Exit(1)
	}

	newRelicExporter := exporters.NewNewRelicExporter(
		"newrelic-api",
		i.Name,
		i.Id,
		i.NrClient,
		i.GetLicenseKey(),
		i.GetRegion(),
		i.DryRun,
	)

	ep := pipeline.NewEventsPipeline("sfdc-events-pipeline")
	ep.AddExporter(newRelicExporter)

	sfdcReceiver, err := NewSalesforceEventsReceiver(i)
	if err != nil {
		log.Errorf("Error creating Salesforce event receiver = %s", err)
		os.Exit(1)
	}

	ep.AddReceiver(sfdcReceiver)

	i.AddComponent(ep)

	// Run the integration
	defer i.Shutdown(ctx)
 	err = i.Run(ctx)
	if err != nil {
		log.Errorf("Error running Salesforce intergation = %s", err)
		os.Exit(1)
	}

	fmt.Printf("-----> END integration")
}
