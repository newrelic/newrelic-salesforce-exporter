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

type SalesforceReceiverInterface interface {
	getConfig() *config.EventLogInstance
	getDB() cache.Cache
}

type DataSenderInterface interface {
	buildCsvLine(fields []string, line []string) any
	buildCustom(record map[string]any, timestampAttr string) any
	send(any)
}

/// Logs receiver struct and LogsReceiver interface implementation

type SalesforceLogsReceiver struct {
	i              *integration.LabsIntegration
	instanceConfig *config.EventLogInstance
	//TODO: use a ref
	db cache.Cache
}

func (s *SalesforceLogsReceiver) GetId() string {
	return "salesforce-logs-receiver"
}

func (s *SalesforceLogsReceiver) PollLogs(context context.Context, writer chan<- model.Log) error {
	log.Debugf("-----> PollLogs for instance '%s'", s.instanceConfig.Name)

	poll(s, &LogsSender{writer})

	log.Debugf("-----> END PollLogs for instance '%s'", s.instanceConfig.Name)
	return nil
}

/// Logs sender implementation of SalesforceReceiverInterface

func (s *SalesforceLogsReceiver) getConfig() *config.EventLogInstance {
	return s.instanceConfig
}

func (s *SalesforceLogsReceiver) getDB() cache.Cache {
	return s.db
}

/// DataSenderInterface for logs

type LogsSender struct {
	writer chan<- model.Log
}

func (s *LogsSender) buildCsvLine(fields []string, line []string) any {
	data := buildCsvLineData(fields, line)
	return data.buildLog()
}

func (s *LogsSender) buildCustom(record map[string]any, timestampAttr string) any {
	data := buildCustomData(record, timestampAttr)
	return data.buildLog()
}

func (s *LogsSender) send(data any) {
	logData, ok := data.(model.Log)
	if ok {
		s.writer <- logData
	} else {
		log.Errorf("Log sender received a data object that is not a model.Log: %v", data)
	}
}

/// Events receiver struct and EventsReceiver interface implementation

type SalesforceEventsReceiver struct {
	i              *integration.LabsIntegration
	instanceConfig *config.EventLogInstance
	//TODO: use a ref
	db cache.Cache
}

func (s *SalesforceEventsReceiver) GetId() string {
	return "salesforce-events-receiver"
}

func (s *SalesforceEventsReceiver) PollEvents(context context.Context, writer chan<- model.Event) error {
	log.Debugf("-----> PollEvents for instance '%s'", s.instanceConfig.Name)

	poll(s, &EventsSender{writer})

	log.Debugf("-----> END PollEvents for instance '%s'", s.instanceConfig.Name)
	return nil
}

/// Events sender implementation of SalesforceReceiverInterface

func (s *SalesforceEventsReceiver) getConfig() *config.EventLogInstance {
	return s.instanceConfig
}

func (s *SalesforceEventsReceiver) getDB() cache.Cache {
	return s.db
}

/// DataSenderInterface for events

type EventsSender struct {
	writer chan<- model.Event
}

func (s *EventsSender) buildCsvLine(fields []string, line []string) any {
	data := buildCsvLineData(fields, line)
	return data.buildEvent()
}

func (s *EventsSender) buildCustom(record map[string]any, timestampAttr string) any {
	data := buildCustomData(record, timestampAttr)
	return data.buildEvent()
}

func (s *EventsSender) send(data any) {
	event, ok := data.(model.Event)
	if ok {
		s.writer <- event
	} else {
		log.Errorf("Event sender received a data object that is not an model.Event: %v", data)
	}
}

/// Generic data builder

type GenericSample struct {
	message    string
	attributes map[string]any
	timestamp  time.Time
}

func (s *GenericSample) buildEvent() model.Event {
	return model.NewEvent(s.message, s.attributes, s.timestamp)
}

func (s *GenericSample) buildLog() model.Log {
	return model.NewLog(s.message, s.attributes, s.timestamp)
}

func buildCsvLineData(fields []string, line []string) GenericSample {
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
	return GenericSample{eventType, attr, timestamp}
}

func buildCustomData(record map[string]any, timestampAttr string) GenericSample {
	eventType := "SFDCUndefinedEvent"
	timestamp := time.Now()
	ts, tsPresent := record[timestampAttr].(string)
	if tsPresent {
		layout := "2006-01-02T15:04:05.999999-0700"
		ts, err := time.Parse(layout, ts)
		if err == nil {
			timestamp = ts
			delete(record, timestampAttr)
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
	delete(record, "attributes")
	return GenericSample{eventType, record, timestamp}
}

// Generic poll function, to be used in both receivers (events and logs)
func poll(s SalesforceReceiverInterface, sender DataSenderInterface) error {
	log.Debugf("-----> Poll for instance '%s'", s.getConfig().Name)

	since := getTimeRange(s)
	until := time.Now()
	setLastRunIntoCache(s, until)

	if !s.getConfig().SkipLogFiles {
		log.Debugf("Request logs since: %v", since)

		response, err := query.RequestLogFiles(s.getConfig(), s.getDB(), since, until)
		if err != nil {
			log.Errorf("Error quering log files, skipping: %s", err.Error())
		} else {
			log.Debugf("Read %d records", len(response.Records))

			processLogFilesResponse(s, &response, sender)
		}
	}

	for _, customQuery := range s.getConfig().CustomQueries {
		log.Debugf("Custom query = %+v", customQuery)

		response, err := query.RequestCustomQuery(&customQuery, s.getConfig(), s.getDB(), since, until)
		log.Debugf("%v", response)
		if err != nil {
			log.Errorf("Error in custom query: %s", err.Error())
			continue
		}

		processEventResponse(s, &response, sender, &customQuery)
	}

	log.Debugf("-----> END Poll for instance '%s'", s.getConfig().Name)

	return nil
}

func getTimeRange(s SalesforceReceiverInterface) time.Time {
	if lastRunExistsInCache(s) {
		return getLastRunFromCache(s)
	} else {
		// If last_run_ts not set, use a fixed interval
		timeInterval := s.getConfig().InitialTimeInterval
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

func lastRunExistsInCache(s SalesforceReceiverInterface) bool {
	val, err := s.getDB().GetCacheVal(lastRunCacheKey(s))
	if err != nil {
		return false
	}
	_, ok := val.(string)
	return ok
}

func getLastRunFromCache(s SalesforceReceiverInterface) time.Time {
	val, err := s.getDB().GetCacheVal(lastRunCacheKey(s))
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

func setLastRunIntoCache(s SalesforceReceiverInterface, ts time.Time) {
	tsStr := strconv.FormatInt(ts.UnixMilli(), 10)
	err := s.getDB().SetCacheVal(lastRunCacheKey(s), tsStr)
	if err != nil {
		log.Errorf("Error setting 'last_run_ts' into cache: %s", err.Error())
	}
}

func lastRunCacheKey(s SalesforceReceiverInterface) string {
	return s.getConfig().Name + "_last_run_ts"
}

func sendCsv(csvContext *CsvContext, sender DataSenderInterface) {
	log.Debugf("Sending %d lines...", len(csvContext.Lines))
	for _, line := range csvContext.Lines {
		data := sender.buildCsvLine(csvContext.Labels, line)
		sender.send(data)
		log.Debugf("NEW SAMPLE -> %#v", data)
	}
	// Clear lines
	csvContext.Lines = [][]string{}
	log.Debugf("Finished sending CSV lines")
}

func processLogFilesResponse(s SalesforceReceiverInterface, response *query.EventLogfileResponse, sender DataSenderInterface) {
	totalEventsSent := 0

	// Download CSV files
	filePaths := downloadCsvFiles(s, response)

	// Parse CSV and generate events
	for _, filePath := range filePaths {
		log.Debugf("Parrse a CSV file: %s", filePath)
		csvContext, err := parseCsvFile(filePath)
		if err != nil {
			break
		}
		for {
			csvContext, err = readCsvData(csvContext)
			if err != nil {
				break
			}

			totalEventsSent += len(csvContext.Lines)

			sendCsv(csvContext, sender)

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

func downloadCsvFiles(s SalesforceReceiverInterface, response *query.EventLogfileResponse) []string {
	// Download CSV files
	filePaths := []string{}
	for _, record := range response.Records {
		if notCached(s, record.Id) {
			filePath, err := query.DownloadCsvFile(s.getConfig(), s.getDB(), &record)
			if err != nil {
				log.Errorf("Error downloading CSV: %s", err.Error())
			} else {
				log.Debugf("Downloaded file at '%s'", filePath)
				filePaths = append(filePaths, filePath)
				addToCache(s, record.Id)
			}
		} else {
			log.Debugf("Logs already processed, ignoring (Id = %s)", record.Id)
		}
	}
	return filePaths
}

func parseCsvFile(filePath string) (*CsvContext, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return &CsvContext{}, err
	}

	csvReader := csv.NewReader(bufio.NewReader(file))

	// Only read the first line, which contains the column names
	labels, err := csvReader.Read()
	if err != nil {
		return &CsvContext{}, err
	}

	csvContext := NewCsvContext(labels, csvReader)

	return &csvContext, nil
}

func readCsvData(csvContext *CsvContext) (*CsvContext, error) {
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

// Check if log ID is present in the cache (was already sent)
func notCached(s SalesforceReceiverInterface, id string) bool {
	val, err := s.getDB().GetCacheVal(id)
	if err != nil {
		log.Warnf("Error accessing the cache: %s", err.Error())
		return true
	}
	return val == nil
}

func addToCache(s SalesforceReceiverInterface, id string) {
	err := s.getDB().SetCacheVal(id, 1)
	if err != nil {
		log.Warnf("Error setting log Id in the cache: %s", err.Error())
	}
}

func processEventResponse(s SalesforceReceiverInterface, response *query.GenericEventResponse, sender DataSenderInterface, customQuery *config.CustomQueryConfig) {
	totalEventsSent := 0

	for _, record := range response.Records {
		id, idPresent := record["Id"].(string)
		if idPresent {
			if notCached(s, id) {
				data := sender.buildCustom(record, customQuery.Timestamp)
				sender.send(data)
				addToCache(s, id)
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

func NewSalesforceEventsReceiver(i *integration.LabsIntegration, instanceConfig *config.EventLogInstance, db cache.Cache) (pipeline.EventsReceiver, error) {
	return &SalesforceEventsReceiver{
		i:              i,
		instanceConfig: instanceConfig,
		db:             db,
	}, nil
}

func NewSalesforceLogsReceiver(i *integration.LabsIntegration, instanceConfig *config.EventLogInstance, db cache.Cache) (pipeline.LogsReceiver, error) {
	return &SalesforceLogsReceiver{
		i:              i,
		instanceConfig: instanceConfig,
		db:             db,
	}, nil
}

type CsvContext struct {
	Labels    []string
	Lines     [][]string
	DidFinish bool
	Reader    *csv.Reader
}

func NewCsvContext(labels []string, reader *csv.Reader) CsvContext {
	return CsvContext{
		Labels:    labels,
		Lines:     [][]string{},
		DidFinish: false,
		Reader:    reader,
	}
}
