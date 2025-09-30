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

	// Read external query files and merge them into the main config
	for index := range integrationConf.EventLog.Instances {
		instance := &integrationConf.EventLog.Instances[index]
		queries, err := eventlog.ParseQueryFiles(instance.CustomQueries.Files, instance.ApiVer)
		if err != nil {
			log.Errorf("Error parsing external query files = %s", err)
			os.Exit(1)
		}
		instance.CustomQueries.Queries = append(instance.CustomQueries.Queries, queries...)
	}

	if err := eventlog.IntegrityCheck(&integrationConf); err != nil {
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

	switch integrationConf.Format {
	case "events":
		log.Debugf("Output data format: Events")
		createEventsPipeline(i, newRelicExporter)
	case "logs":
		log.Debugf("Output data format: Logs")
		createLogsPipeline(i, newRelicExporter)
	default:
		log.Errorf("Format must be either 'events' or 'logs'")
		os.Exit(1)
	}

	// Run the integration
	defer i.Shutdown(ctx)
 	err = i.Run(ctx)
	if err != nil {
		log.Errorf("Error running Salesforce intergation = %s", err)
		os.Exit(1)
	}

	log.Debugf("Finish integration")
}

func createEventsPipeline(i *integration.LabsIntegration, newRelicExporter *exporters.NewRelicExporter) {
	ep := pipeline.NewEventsPipeline("sfdc-events-pipeline")
	ep.AddExporter(newRelicExporter)

	// Add one Salesforce Events Receiver component per instance
	for _, instanceConfig  := range integrationConf.EventLog.Instances {
		db := cache.BuildCache(instanceConfig.Cache)
		sfdcReceiver := eventlog.NewSalesforceEventsReceiver(i, &instanceConfig, db)
		ep.AddReceiver(sfdcReceiver)
	}

	i.AddComponent(ep)
}

func createLogsPipeline(i *integration.LabsIntegration, newRelicExporter *exporters.NewRelicExporter) {
	ep := pipeline.NewLogsPipeline("sfdc-logs-pipeline")
	ep.AddExporter(newRelicExporter)

	// Add one Salesforce Logs Receiver component per instance
	for _, instanceConfig  := range integrationConf.EventLog.Instances {
		db := cache.BuildCache(instanceConfig.Cache)
		sfdcReceiver := eventlog.NewSalesforceLogsReceiver(i, &instanceConfig, db)
		ep.AddReceiver(sfdcReceiver)
	}

	i.AddComponent(ep)
}