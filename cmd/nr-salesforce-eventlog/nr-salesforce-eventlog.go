package main

import (
	"context"
	"os"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/exporters"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/pipeline"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/eventlog"
)

const (
	INTEGRATION_ID   = "com.newrelic.salesforce.eventlog"
	INTEGRATION_NAME = "New Relic Salesforce Event Log"
	DEFAULT_INTERVAL = 5
)

var integrationConf config.Config

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

	integrationConf, err = config.ReadConfig()
	if err != nil {
		log.Errorf("Error loading config = %s", err)
		os.Exit(1)
	}

	if err := eventlog.IntegrityCheck(integrationConf); err != nil {
		log.Errorf("Error checking config integrity = %s", err)
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

	// Add one Salesforce Events Receiver component per instance
	for _, instanceConfig  := range integrationConf.EventLog.Instances {
		db := cache.BuildCache(instanceConfig.Cache)
		sfdcReceiver, err := eventlog.NewSalesforceEventsReceiver(i, &instanceConfig, db)
		if err != nil {
			log.Errorf("Error creating Salesforce event receiver = %s", err)
			os.Exit(1)
		}
		ep.AddReceiver(sfdcReceiver)
	}

	i.AddComponent(ep)

	// Run the integration
	defer i.Shutdown(ctx)
 	err = i.Run(ctx)
	if err != nil {
		log.Errorf("Error running Salesforce intergation = %s", err)
		os.Exit(1)
	}

	log.Debugf("Finish integration")
}
