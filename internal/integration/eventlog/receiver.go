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
)

const MaxLinesToRead = 100

//TODO: implement LogsReceiver to generate logs when config format = "logs"

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

	since := s.getTimeRange()
	until := time.Now()
	s.setLastRunIntoCache(until)

	if !s.instanceConfig.SkipLogFiles {
		log.Debugf("Request logs since: %v", since)

		response, err := query.RequestLogFiles(s.instanceConfig, s.db, since, until)
		if err != nil {
			log.Errorf("Error quering log files, skipping: %s", err.Error())
		} else {
			log.Debugf("Read %d records", len(response.Records))

			s.processLogFilesResponse(&response, writer)
		}
	}

	for _, customQuery := range s.instanceConfig.CustomQueries {
		log.Debugf("Custom query = %+v", customQuery)

		response, err := query.RequestCustomQuery(&customQuery, s.instanceConfig, s.db, since, until)
		if err != nil {
			log.Errorf("Error in custom query: %s", err.Error())
			continue
		}

		s.processEventResponse(&response, writer, &customQuery)
	}

	log.Debugf("-----> END PollEvents for instance '%s'", s.instanceConfig.Name)

	return nil	
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

func (s *SalesforceEventsReceiver) processLogFilesResponse(response *query.EventLogfileResponse, writer chan <- model.Event) {
	totalEventsSent := 0

	// Download CSV files
	filePaths := s.downloadCsvFiles(response)

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

	log.Debugf("Total logfile events sent = %d", totalEventsSent)

	// Delete all temp CSV files
	for _, filePath := range filePaths {
		err := os.Remove(filePath)
    	if err != nil {
        	log.Errorf("Error deleting CSV file: %s", err.Error())
		}
	}
}

func (s *SalesforceEventsReceiver) processEventResponse(response *query.GenericEventResponse, writer chan <- model.Event, customQuery *config.CustomQueryConfig) {
	totalEventsSent := 0

	for _, record := range response.Records {
		id, idPresent := record["Id"].(string)
		if idPresent {
			if s.notCached(id) {
				event := s.buildCustomEventFrom(record, customQuery.Timestamp)
				writer <- event
				s.addToCache(id)
				totalEventsSent += 1
			} else {
				log.Debugf("Event already processed, ignoring (Id = %s)", id)
			}
		} else {
			log.Warnf("Event does not have an 'Id' field, ignoring")
		}
	}

	log.Debugf("Total events sent = %d", totalEventsSent)
}

func (s *SalesforceEventsReceiver) buildCustomEventFrom(record map[string]any, timestampAttr string) model.Event {
	eventType := "SFDCUndefinedEvent"
	timestamp := time.Now()
	ts, tsPresent := record[timestampAttr].(string)
	if tsPresent {
		layout := "2006-01-02T15:04:05.999999-0700"
		ts, err := time.Parse(layout, ts)
		if err == nil {
			timestamp = ts
			delete(record, timestampAttr);
		} else {
			log.Errorf("'%s' parsing failed, using 'now'", timestampAttr)
		}
	}
	attributes, attrPresent := record["attributes"].(map[string]any)
	if attrPresent {
		attrType, attrTypePresent := attributes["type"].(string)
		if attrTypePresent {
			eventType = attrType
		} else {
			log.Warnf("Event does not have an 'attributes.type' key")
		}
	} else {
		log.Warnf("Event does not have an 'attributes' key")
	}
	delete(record, "attributes");
	return model.NewEvent(eventType, record, timestamp)
}

func (s *SalesforceEventsReceiver) downloadCsvFiles(response *query.EventLogfileResponse) []string {
	// Download CSV files
	filePaths := []string{}
	for _, record := range response.Records {
		if s.notCached(record.Id) {
			filePath, err := query.DownloadCsvFile(s.instanceConfig, s.db, &record)
			if err != nil {
				log.Errorf("Error downloading CSV: %s", err.Error())
			} else {
				log.Debugf("Downloaded file at '%s'", filePath)
				filePaths = append(filePaths, filePath)
				s.addToCache(record.Id)
			}
		} else {
			log.Debugf("Logs already processed, ignoring (Id = %s)", record.Id)
		}
	}
	return filePaths
}

// Check if log ID is present in the cache (was already sent)
func (s *SalesforceEventsReceiver) notCached(id string) bool {
	val, err := s.db.GetCacheVal(id)
	if err != nil {
		log.Warnf("Error accessing the cache: %s", err.Error())
		return true
	}
	return val == nil
}

func (s *SalesforceEventsReceiver) addToCache(id string) {
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