package eventlog

import (
	"context"
	"os"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/model"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/pipeline"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/oauth"
)

type SalesforceEventsReceiver struct {
	i *integration.LabsIntegration
	instanceConfig *config.EventLogInstance
}

func (s *SalesforceEventsReceiver) GetId() string {
	return "salesforce-events-receiver"
}

func (s *SalesforceEventsReceiver) PollEvents(context context.Context, writer chan <- model.Event) error {
	//TODO: send events
	log.Debugf("-----> PollEvents for instance '%s'", s.instanceConfig.Name)

	// TEST auth
	login, err := oauth.Login(s.instanceConfig.Auth)
	if err != nil {
		log.Errorf("Error loging in = %s", err)
		os.Exit(1)
	}
	log.Debugf("Token type = %v", login.TokenType)
	log.Debugf("Access token = %v", login.AccessToken)

	log.Debugf("-----> END PollEvents for instance '%s'", s.instanceConfig.Name)

	return nil	
}

func NewSalesforceEventsReceiver(i *integration.LabsIntegration, instanceConfig *config.EventLogInstance) (pipeline.EventsReceiver, error) {
	return &SalesforceEventsReceiver{
		i: i,
		instanceConfig: instanceConfig,
	}, nil
}

	//TODO: create a receiver for hourly event logs
	//TODO: create a receiver for generic queries in SOQL
	//TODO: try using the NewSimpleReceiver first, or use a custom Http Connector (NewHttpMETHODConnector).

	/* API interactions:
	- Authenticate
	- Refresh token
	- Get hourly event logs (JSON, list of log files)
	- Download log files in CSV
	- Run SOQL request
	*/
	// SOQL request example (EventLogFile):
	/*
		curl "https://newrelic-neworg--staging.sandbox.my.salesforce.com/services/data/v64.0/query?q=SELECT+Id+,+EventType+,+Interval+,+LogDate+,+LogFile+FROM+EventLogFile+WHERE+EventType+=+'URI'+AND+Interval+=+'Hourly'"
		-H "Authorization: Bearer MY_TOKEN_HERE"
	*/
	// Download log file example:
	/*
		curl "https://newrelic-neworg--staging.sandbox.my.salesforce.com/services/data/v64.0/sobjects/EventLogFile/0ATO3000008PuoYOAS/LogFile"
		-H "Authorization: Bearer MY_TOKEN_HERE"
	*/
