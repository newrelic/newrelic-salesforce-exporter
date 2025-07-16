package eventlog

import (
	"context"
	"time"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/model"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/pipeline"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/eventlog/query"
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

	//TODO: check if there is a token in the cache for current instance
	//TODO: if not present: Login, store the token, and try the request
	//TODO: 	if ok: process the response
	//TODO: 	if error: print error, abort
	//TODO: if present: try the request with this token
	//TODO: 	if ok: process the response
	//TODO: 	if 401 error: Login, store the token, retry request
	//TODO: 	if other error: print error, abort

	
	// TEST: login and request log files since 4 hours ago

	login, err := oauth.Login(s.instanceConfig.Auth)
	if err != nil {
		return err
	}

	log.Debugf("Token type = %v", login.TokenType)
	log.Debugf("Access token = %v", login.AccessToken)

	since := time.Now().Add(-time.Hour * 4)
	until := time.Now()
	response, err := query.RequestLogFiles(s.instanceConfig, login.AccessToken, since, until)
	if err != nil {
		return err
	}

	log.Debugf("-----> Response = '%#+v'", response)

	//TODO: build events and send them through the "write" channel

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
- Authenticate (UserPass, JWT, and maybe also Client Credentials)
- Get hourly event logs (JSON, list of log files)
- Download log files in CSV
- Run SOQL request
*/
// SOQL request example (EventLogFile):
/*
	curl "https://newrelic-neworg--staging.sandbox.my.salesforce.com/services/data/v64.0/query?q=SELECT+Id+,+EventType+,+Interval+,+LogDate+,+LogFile+FROM+EventLogFile+WHERE+EventType+=+'URI'+AND+Interval+=+'Hourly'+AND+LogDate+>+2025-07-14T23:00:00Z"
	-H "Authorization: Bearer MY_TOKEN_HERE"
*/
// Download log file example:
/*
	curl "https://newrelic-neworg--staging.sandbox.my.salesforce.com/services/data/v64.0/sobjects/EventLogFile/0ATO3000008PuoYOAS/LogFile"
	-H "Authorization: Bearer MY_TOKEN_HERE"
*/

//Auth flows:
// Username-Password: https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_username_password_flow.htm&type=5
// JWT: https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_jwt_flow.htm&type=5
// Client credentials: https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_client_credentials_flow.htm&type=5

// Only JWT supports token refresh