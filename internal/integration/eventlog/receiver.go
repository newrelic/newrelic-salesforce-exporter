package eventlog

import (
	"context"
	"time"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/model"
	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/pipeline"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/eventlog/query"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/oauth"
)

type SalesforceEventsReceiver struct {
	i *integration.LabsIntegration
	instanceConfig *config.EventLogInstance
	db cache.Cache
}

func (s *SalesforceEventsReceiver) GetId() string {
	return "salesforce-events-receiver"
}

func (s *SalesforceEventsReceiver) PollEvents(context context.Context, writer chan <- model.Event) error {
	log.Debugf("-----> PollEvents for instance '%s'", s.instanceConfig.Name)

	var accessToken string

	val, err := s.db.GetCacheVal(tokenCacheKey(s.instanceConfig))
	if err != nil {
		log.Errorf("Error getting token from cache: %s", err.Error())
	}

	valStr, ok := val.(string)
	if ok {
		log.Debugf("Got token from cache, skip login")
		accessToken = valStr
	} else {
		log.Debugf("No token in cache, login")
		login, err := oauth.Login(s.instanceConfig.Auth)
		if err != nil {
			return err
		}
		
		accessToken = login.AccessToken

		err = s.db.SetCacheVal(tokenCacheKey(s.instanceConfig), accessToken)
		if err != nil {
			log.Errorf("Error setting token into cache: %s", err.Error())
		}
	}
	
	log.Debugf("Access token = %s", accessToken)

	//TODO: get actual time range from the config
	since := time.Now().Add(-time.Hour * 4)
	until := time.Now()
	
	var response query.EventLogfileResponse

	response, err = query.RequestLogFiles(s.instanceConfig, accessToken, since, until)
	if err != nil {
		// Is 401 error, relogin and retry request
		if query.IsReloginError(err) {
			log.Debugf("Wrong credentials error (401). Try relogin...")
			login, err := oauth.Login(s.instanceConfig.Auth)
			if err != nil {
				return err
			}
			response, err = query.RequestLogFiles(s.instanceConfig, login.AccessToken, since, until)
			if err != nil {
				return err
			}
		} else {
			return err
		}
	}

	log.Debugf("-----> Response = '%#+v'", response)

	//TODO: download CSV files
	//TODO: generate events from each log line
	//TODO: de-duplicate using cache
	//TODO: send events through the "write" channel

	log.Debugf("-----> END PollEvents for instance '%s'", s.instanceConfig.Name)

	return nil	
}

func NewSalesforceEventsReceiver(i *integration.LabsIntegration, instanceConfig *config.EventLogInstance, db cache.Cache) (pipeline.EventsReceiver, error) {
	return &SalesforceEventsReceiver{
		i: i,
		instanceConfig: instanceConfig,
		db: db,
	}, nil
}

func tokenCacheKey(instanceConfig *config.EventLogInstance) string {
	return instanceConfig.Name + "_access_token"
}

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