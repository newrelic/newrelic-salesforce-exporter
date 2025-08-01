package eventlog

import (
	"bufio"
	"context"
	"encoding/csv"
	"io"
	"os"
	"strconv"
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

const MaxLinesToRead = 100

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

	accessToken, err := s.auth()
	if err != nil {
		return err
	}

	since := s.getTimeRange()
	until := time.Now()
	s.setLastRunIntoCache(until)

	log.Debugf("Request logs since: %v", since)
	
	var response query.EventLogfileResponse

	//TODO: query any kind of event (custom SOQL). Specify the name of the timestamp attribute (defeault "CreatedAt").

	response, err = query.RequestLogFiles(s.instanceConfig, accessToken, since, until)
	if err != nil {
		// Is 401 error, relogin and retry request
		if query.IsReloginError(err) {
			log.Debugf("Wrong credentials error (401). Try relogin...")

			s.deleteTokenFromCache()
			accessToken, err = s.auth()
			if err != nil {
				return err
			}

			response, err = query.RequestLogFiles(s.instanceConfig, accessToken, since, until)
			if err != nil {
				return err
			}
		} else {
			return err
		}
	}

	log.Debugf("Read %d records", len(response.Records))

	s.processLogFilesResponse(&response, accessToken, writer)

	log.Debugf("-----> END PollEvents for instance '%s'", s.instanceConfig.Name)

	return nil	
}

// TODO: Support auth flows:
// (alreadys upported) Username-Password: https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_username_password_flow.htm&type=5
// JWT: https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_jwt_flow.htm&type=5
// Client credentials: https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_client_credentials_flow.htm&type=5
// Only JWT supports token refresh

func (s *SalesforceEventsReceiver) auth() (string, error) {
	accessToken, ok := s.getTokenFromCache().(string)
	if ok {
		log.Debugf("Got token from cache, skip login")
		return accessToken, nil
	} else {
		log.Debugf("No token in cache, login")
		login, err := oauth.Login(s.instanceConfig.Auth)
		if err != nil {
			return "", err
		}
		s.setTokenIntoCache(login.AccessToken)
		return login.AccessToken, nil
	}
}

func (s *SalesforceEventsReceiver) getTokenFromCache() any {
	val, err := s.db.GetCacheVal(s.tokenCacheKey())
	if err != nil {
		log.Errorf("Error getting token from cache: %s", err.Error())
	}
	return val
}

func (s *SalesforceEventsReceiver) setTokenIntoCache(accessToken string) {
	err := s.db.SetCacheVal(s.tokenCacheKey(), accessToken)
	if err != nil {
		log.Errorf("Error setting token into cache: %s", err.Error())
	}
}

func (s *SalesforceEventsReceiver) deleteTokenFromCache() {
	err := s.db.DelCacheVal(s.tokenCacheKey())
	if err != nil {
		log.Errorf("Error deleting token from cache: %s", err.Error())
	}
}

func (s *SalesforceEventsReceiver) tokenCacheKey() string {
	return s.instanceConfig.Name + "_access_token"
}

func (s *SalesforceEventsReceiver) getTimeRange() time.Time {
	if s.lastRunExistsInCache() {
		return s.getLastRunFromCache()
	} else {
		// If last_run_ts not set, use a fixed interval
		timeInterval := s.instanceConfig.InitialTimeInterval
		if timeInterval.Hours == 0 && timeInterval.Minutes == 0 {
			// If not defined, use 1 hour ago as default value
			return time.Now().Add(-time.Minute * 60)
		} else {
			return time.Now().Add(
					-time.Minute * time.Duration(timeInterval.Minutes),
				).Add(
					-time.Hour * time.Duration(timeInterval.Hours),
				)
		}
	}
}

func (s *SalesforceEventsReceiver) lastRunExistsInCache() bool {
	val, err := s.db.GetCacheVal(s.lastRunCacheKey())
	if err != nil {
		return false
	}
	_, ok := val.(string)
	return ok
}

func (s *SalesforceEventsReceiver) getLastRunFromCache() time.Time {
	val, err := s.db.GetCacheVal(s.lastRunCacheKey())
	if err != nil {
		log.Errorf("Error getting 'last_run_ts' from cache: %s", err.Error())
	}
	valStr, ok := val.(string)
	if !ok {
		return time.UnixMilli(0)
	}
	tsInt, err := strconv.ParseInt(valStr, 10, 64)
	if err != nil {
		return time.UnixMilli(0)
	}
	tsTime := time.UnixMilli(tsInt)
	return tsTime
}

func (s *SalesforceEventsReceiver) setLastRunIntoCache(ts time.Time) {
	tsStr := strconv.FormatInt(ts.UnixMilli(), 10)
	err := s.db.SetCacheVal(s.lastRunCacheKey(), tsStr)
	if err != nil {
		log.Errorf("Error setting 'last_run_ts' into cache: %s", err.Error())
	}
}

func (s *SalesforceEventsReceiver) lastRunCacheKey() string {
	return s.instanceConfig.Name + "_last_run_ts"
}

func (s *SalesforceEventsReceiver) processLogFilesResponse(response *query.EventLogfileResponse, accessToken string, writer chan <- model.Event) {
	totalEventsSent := 0

	// Download CSV files
	filePaths := s.downloadCsvFiles(response, accessToken)

	// Parse CSV and generate events
	for _, filePath := range filePaths {
		log.Debugf("Parrse a CSV file: %s", filePath)
		csvContext, err := s.parseCsvFile(filePath)
		if err != nil {
			break
		}
		for {
			csvContext, err = s.readCsvData(csvContext)
			if err != nil {
				break
			}
			
			totalEventsSent += len(csvContext.Lines)

			s.sendEvents(csvContext, writer)

			if csvContext.DidFinish {
				break
			}
		}
	}

	log.Debugf("Total events sent = %d", totalEventsSent)

	// Delete all temp CSV files
	for _, filePath := range filePaths {
		err := os.Remove(filePath)
    	if err != nil {
        	log.Errorf("Error deleting CSV file: %s", err.Error())
		}
	}
}

func (s *SalesforceEventsReceiver) downloadCsvFiles(response *query.EventLogfileResponse, accessToken string) []string {
	// Download CSV files
	filePaths := []string{}
	for _, record := range response.Records {
		if s.logsNotCached(record.Id) {
			filePath, err := query.DownloadCsvFile(s.instanceConfig.Auth.TokenUrl, &record, accessToken)
			if err != nil {
				log.Errorf("Error downloading CSV: %s", err.Error())
			} else {
				log.Debugf("Downloaded file at '%s'", filePath)
				filePaths = append(filePaths, filePath)
				s.cachedLog(record.Id)
			}
		} else {
			log.Debugf("Logs already processed, ignoring (Id = %s)", record.Id)
		}
	}
	return filePaths
}

// Check if log ID is present in the cache (was already sent)
func (s *SalesforceEventsReceiver) logsNotCached(id string) bool {
	val, err := s.db.GetCacheVal(id)
	if err != nil {
		log.Warnf("Error accessing the cache: %s", err.Error())
		return true
	}
	return val == nil
}

func (s *SalesforceEventsReceiver) cachedLog(id string) {
	err := s.db.SetCacheVal(id, 1)
	if err != nil {
		log.Warnf("Error setting log Id in the cache: %s", err.Error())
	}
}

func (s *SalesforceEventsReceiver) parseCsvFile(filePath string) (*CsvContext, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return &CsvContext{}, err
	}

	csvReader := csv.NewReader(bufio.NewReader(file))

	// Only read the first line, which contains the column names
	labels, err := csvReader.Read()
	if err != nil  {
		return &CsvContext{}, err
	}

	csvContext := NewCsvContext(labels, csvReader)
	
	return &csvContext, nil
}

func (s *SalesforceEventsReceiver) readCsvData(csvContext *CsvContext) (*CsvContext, error) {
	log.Debugf("Reading a batch of CSV lines...")
	for range MaxLinesToRead {
		record, err := csvContext.Reader.Read()
		if err == io.EOF {
			csvContext.DidFinish = true
			break
		}
		if err != nil {
			log.Errorf("Error parsing CSV: %s", err.Error())
			return csvContext, err
		}

		//log.Debugf("-> CSV Record: %v", record)

		csvContext.Lines = append(csvContext.Lines, record)
	}
	log.Debugf("Read %d lines. Finished? %t", len(csvContext.Lines), csvContext.DidFinish)
	return csvContext, nil
}

func (s *SalesforceEventsReceiver) sendEvents(csvContext *CsvContext, writer chan <- model.Event) {
	log.Debugf("Sending %d events...", len(csvContext.Lines))
	for _, line := range csvContext.Lines {
		event := s.buildEventFromCsvLine(csvContext.Labels, line)
		writer <- event
		log.Debugf("NEW EVENT -> %#v", event)
	}
	// Clear lines
	csvContext.Lines = [][]string{}
	log.Debugf("Finished sending events")
}

func (s *SalesforceEventsReceiver) buildEventFromCsvLine(fields []string, line []string) model.Event {
	eventType := "SFDCUndefinedEvent"
	timestamp := time.Now()
	attr := map[string]any{}
	for index, label := range fields {
		switch label {
		case "EVENT_TYPE":
			eventType = "SFDC" + line[index]
		case "TIMESTAMP":
			layout := "20060102150405.999999"
			ts, err := time.Parse(layout, line[index])
			if err == nil {
				timestamp = ts
			} else {
				log.Errorf("TIMESTAMP parsing failed, using 'now'")
			}
		default:
			attr[label] = line[index]
		}
	}
	return model.NewEvent(eventType, attr, timestamp)
}

func NewSalesforceEventsReceiver(i *integration.LabsIntegration, instanceConfig *config.EventLogInstance, db cache.Cache) (pipeline.EventsReceiver, error) {
	return &SalesforceEventsReceiver{
		i: i,
		instanceConfig: instanceConfig,
		db: db,
	}, nil
}

type CsvContext struct {
	Labels []string
	Lines [][]string
	DidFinish bool
	Reader *csv.Reader
}

func NewCsvContext(labels []string, reader *csv.Reader) CsvContext {
	return CsvContext {
		Labels: labels,
		Lines: [][]string{},
		DidFinish: false,
		Reader: reader,
	}
}