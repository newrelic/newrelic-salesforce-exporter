package eventlog

import (
	"bufio"
	"context"
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"fmt"
	"io"
	"maps"
	"os"
	"strconv"
	"strings"
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
const LogDateFormat = "2006-01-02T15:04:05.999999-0700"

type FieldMapping = map[string]bool

type CsvFile struct {
	FilePath     string
	EventType    string
	FieldMapping FieldMapping
}

type SalesforceReceiverInterface interface {
	getConfig() *config.EventLogConfig
	getDB() cache.Cache
}

type DataSenderInterface interface {
	buildCsvLine(fields []string, line []string, fieldMaping FieldMapping) any
	buildCustom(record map[string]any, timestampAttr string) any
	buildLimit(name string, limit query.SingleLimitResponse) any
	send(any)
}

/// Logs receiver struct and LogsReceiver interface implementation

type SalesforceLogsReceiver struct {
	i              *integration.LabsIntegration
	instanceConfig *config.EventLogConfig
	db             cache.Cache
}

func (s *SalesforceLogsReceiver) GetId() string {
	return "salesforce-logs-receiver"
}

func (s *SalesforceLogsReceiver) PollLogs(context context.Context, writer chan<- model.Log) error {
	return poll(s, &LogsSender{writer, buildDefaultAttributes(s)})
}

/// Logs sender implementation of SalesforceReceiverInterface

func (s *SalesforceLogsReceiver) getConfig() *config.EventLogConfig {
	return s.instanceConfig
}

func (s *SalesforceLogsReceiver) getDB() cache.Cache {
	return s.db
}

/// DataSenderInterface for logs

type LogsSender struct {
	writer     chan<- model.Log
	Attributes map[string]any
}

func (s *LogsSender) buildCsvLine(fields []string, line []string, fieldMapping FieldMapping) any {
	data := buildCsvLineData(fields, line, fieldMapping)
	return data.buildLog()
}

func (s *LogsSender) buildCustom(record map[string]any, timestampAttr string) any {
	data := buildCustomData(record, timestampAttr)
	return data.buildLog()
}

func (s *LogsSender) buildLimit(name string, limit query.SingleLimitResponse) any {
	data := buildLimit(name, limit)
	return data.buildLog()
}

func (s *LogsSender) send(data any) {
	logData, ok := data.(model.Log)
	if ok {
		maps.Copy(logData.Attributes, s.Attributes)
		s.writer <- logData
	} else {
		log.Errorf("Log sender received a data object that is not a model.Log: %v", data)
	}
}

/// Events receiver struct and EventsReceiver interface implementation

type SalesforceEventsReceiver struct {
	i              *integration.LabsIntegration
	instanceConfig *config.EventLogConfig
	db             cache.Cache
}

func (s *SalesforceEventsReceiver) GetId() string {
	return "salesforce-events-receiver"
}

func (s *SalesforceEventsReceiver) PollEvents(context context.Context, writer chan<- model.Event) error {
	return poll(s, &EventsSender{writer, buildDefaultAttributes(s)})
}

/// Events sender implementation of SalesforceReceiverInterface

func (s *SalesforceEventsReceiver) getConfig() *config.EventLogConfig {
	return s.instanceConfig
}

func (s *SalesforceEventsReceiver) getDB() cache.Cache {
	return s.db
}

/// DataSenderInterface for events

type EventsSender struct {
	writer     chan<- model.Event
	Attributes map[string]any
}

func (s *EventsSender) buildCsvLine(fields []string, line []string, fieldMapping FieldMapping) any {
	data := buildCsvLineData(fields, line, fieldMapping)
	truncLongStrings(&data)
	return data.buildEvent()
}

func (s *EventsSender) buildCustom(record map[string]any, timestampAttr string) any {
	data := buildCustomData(record, timestampAttr)
	truncLongStrings(&data)
	return data.buildEvent()
}

func (s *EventsSender) buildLimit(name string, limit query.SingleLimitResponse) any {
	data := buildLimit(name, limit)
	return data.buildEvent()
}

func (s *EventsSender) send(data any) {
	event, ok := data.(model.Event)
	if ok {
		maps.Copy(event.Attributes, s.Attributes)
		s.writer <- event
	} else {
		log.Errorf("Event sender received a data object that is not a model.Event: %v", data)
	}
}

/// Generic data builder

type GenericSample struct {
	text       string
	attributes map[string]any
	timestamp  time.Time
}

func (s *GenericSample) buildEvent() model.Event {
	return model.NewEvent(s.text, s.attributes, s.timestamp)
}

func (s *GenericSample) buildLog() model.Log {
	return model.NewLog(s.text, s.attributes, s.timestamp)
}

func buildCsvLineData(fields []string, line []string, fieldMapping FieldMapping) GenericSample {
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
			if len(fieldMapping) > 0 && !fieldMapping[label] {
				// This field is not mapped, skip it
				continue
			}
			fieldValue := line[index]
			// Check if it's a numeric field or not
			intField, err := strconv.Atoi(fieldValue)
			if err == nil {
				attr[label] = intField
			} else {
				attr[label] = fieldValue
			}
		}
	}
	return GenericSample{eventType, attr, timestamp}
}

func buildCustomData(record map[string]any, timestampAttr string) GenericSample {
	eventType := "SFDCUndefinedEvent"
	timestamp := time.Now()
	ts, tsPresent := record[timestampAttr].(string)
	if tsPresent {
		ts, err := time.Parse(LogDateFormat, ts)
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
			eventType = "SFDC" + attrType
		} else {
			log.Warnf("Event does not have an 'attributes.type' key")
		}
	} else {
		log.Warnf("Event does not have an 'attributes' key")
	}
	delete(record, "attributes")
	return GenericSample{eventType, record, timestamp}
}

func buildLimit(name string, limit query.SingleLimitResponse) GenericSample {
	data := GenericSample{
		text: "SFDCLimits",
		attributes: map[string]any{
			"limitName":      name,
			"limitMax":       limit.Max,
			"limitRemaining": limit.Remaining,
		},
		timestamp: time.Now(),
	}
	return data
}

func truncLongStrings(sample *GenericSample) {
	if len(sample.text) > 4096 {
		sample.text = sample.text[:4096]
		log.Debugf("Truncate sample 'text' that exceeds the 4096 limit")
	}
	for k := range sample.attributes {
		v, ok := sample.attributes[k].(string)
		if ok {
			if len(v) > 4096 {
				sample.attributes[k] = v[:4096]
				log.Debugf("Truncate attribute '%s' string that exceeds the 4096 limit", k)
			}
		}
	}
}

func buildDefaultAttributes(s SalesforceReceiverInterface) map[string]any {
	return map[string]any{
		"sf.instance.name": s.getConfig().Name,
	}
}

// Generic poll function, to be used in both receivers (events and logs)
func poll(s SalesforceReceiverInterface, sender DataSenderInterface) error {
	log.Debugf("Begin poll for instance '%s'", s.getConfig().Name)

	// Collect event logs
	if !s.getConfig().SkipLogFiles {
		since := getTimeRange(s, lastRunCacheKey(s))
		until := time.Now()

		log.Debugf("Request logs since: %v", since)

		response, err := query.RequestLogFiles(s.getConfig(), s.getDB(), since, until)
		if err != nil {
			log.Errorf("Error quering log files, skipping: %s", err.Error())
		} else {
			log.Debugf("Read %d records", len(response.Records))

			if len(response.Records) > 0 {
				lastLogDate := processLogFilesResponse(s, &response, sender)
				// We to set the time of the last log/event we receive, otherwise we may have data gaps
				setLastRunIntoCache(s, lastLogDate, lastRunCacheKey(s))
			}
		}
	} else {
		// Skip event log files, set last run date to now
		setLastRunIntoCache(s, time.Now(), lastRunCacheKey(s))
	}

	// Collect custom queries data
	if len(s.getConfig().CustomQueries) > 0 {
		since := getTimeRange(s, customQueriesLastRunCacheKey(s))
		until := time.Now()

		for _, customQuery := range s.getConfig().CustomQueries {

			log.Debugf("Custom query = %+v", customQuery)

			response, err := query.RequestCustomQuery(&customQuery, s.getConfig(), s.getDB(), since, until)
			if err != nil {
				log.Errorf("Error in custom query: %s", err.Error())
				continue
			}

			processEventResponse(s, &response, sender, &customQuery)
		}

		setLastRunIntoCache(s, until, customQueriesLastRunCacheKey(s))
	} else {
		// No custom queries, set last run date to now
		setLastRunIntoCache(s, time.Now(), customQueriesLastRunCacheKey(s))
	}

	// Collect org limits
	if !s.getConfig().SkipLimits {
		limits, err := query.RequestLimits(s.getConfig(), s.getDB())
		if err != nil {
			log.Errorf("Error requesting org limis: %s", err.Error())
		} else {
			processLimitsResponse(limits, sender)
		}
	}

	log.Debugf("End poll for instance '%s'", s.getConfig().Name)

	return nil
}

func getTimeRange(s SalesforceReceiverInterface, cacheKey string) time.Time {
	if lastRunExistsInCache(s, cacheKey) {
		return getLastRunFromCache(s, cacheKey)
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

func lastRunExistsInCache(s SalesforceReceiverInterface, cacheKey string) bool {
	val, err := s.getDB().GetCacheVal(cacheKey)
	if err != nil {
		return false
	}
	_, ok := val.(string)
	return ok
}

func getLastRunFromCache(s SalesforceReceiverInterface, cacheKey string) time.Time {
	val, err := s.getDB().GetCacheVal(cacheKey)
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

func setLastRunIntoCache(s SalesforceReceiverInterface, ts time.Time, cacheKey string) {
	tsStr := strconv.FormatInt(ts.UnixMilli(), 10)
	err := s.getDB().SetCacheVal(cacheKey, tsStr)
	if err != nil {
		log.Errorf("Error setting 'last_run_ts' into cache: %s", err.Error())
	}
}

// Last run for EventLogFile queries
func lastRunCacheKey(s SalesforceReceiverInterface) string {
	return s.getConfig().Name + "_last_run_ts"
}

// Last run for custom queries
func customQueriesLastRunCacheKey(s SalesforceReceiverInterface) string {
	return s.getConfig().Name + "_custom_queries_last_run_ts"
}

func sendCsv(csvContext *CsvContext, sender DataSenderInterface, fieldMapping FieldMapping) {
	log.Debugf("Sending %d lines...", len(csvContext.Lines))
	for _, line := range csvContext.Lines {
		data := sender.buildCsvLine(csvContext.Labels, line, fieldMapping)
		sender.send(data)
		log.Debugf("NEW SAMPLE -> %#v", data)
	}
	// Clear lines
	csvContext.Lines = [][]string{}
	log.Debugf("Finished sending CSV lines")
}

func processLogFilesResponse(s SalesforceReceiverInterface, response *query.EventLogfileResponse, sender DataSenderInterface) time.Time {
	totalEventsSent := 0

	// Download CSV files
	csvFiles, lastLogDate := downloadCsvFiles(s, response)

	// Parse CSV and generate events
	for _, csvFile := range csvFiles {
		log.Debugf("Parse a CSV file: %+v", csvFile.FilePath)
		log.Debugf("Field mapping for current file: %+v", csvFile.FieldMapping)

		csvContext, err := parseCsvFile(csvFile)
		if err != nil {
			log.Errorf("CSV header parsing failed: %s", err)
			break
		}
		for {
			csvContext, err = readCsvData(csvContext)
			if err != nil {
				log.Errorf("CSV parsing failed: %s", err)
				break
			}

			totalEventsSent += len(csvContext.Lines)

			sendCsv(csvContext, sender, csvFile.FieldMapping)

			if csvContext.DidFinish {
				break
			}
		}
	}

	log.Debugf("Total logfile events sent = %d", totalEventsSent)

	// Delete all temp CSV files
	for _, csvFile := range csvFiles {
		err := os.Remove(csvFile.FilePath)
		if err != nil {
			log.Errorf("Error deleting CSV file: %s", err.Error())
		}
	}

	return lastLogDate
}

func downloadCsvFiles(s SalesforceReceiverInterface, response *query.EventLogfileResponse) ([]CsvFile, time.Time) {
	// Download CSV files
	csvFiles := []CsvFile{}
	var lastLogDateStr string
	for _, record := range response.Records {
		lastLogDateStr = record.CreatedDate
		log.Debugf("CSV file Id = '%s', CreatedDate = '%s' LogDate = '%s'", record.Id, record.CreatedDate, record.LogDate)
		// De-duplicate log
		if notCached(s, record.Id) {
			filePath, err := query.DownloadCsvFile(s.getConfig(), s.getDB(), &record)
			if err != nil {
				log.Errorf("Error downloading CSV: %s", err.Error())
			} else {
				log.Debugf("Downloaded file at '%s'", filePath)
				csvFiles = append(csvFiles, buildCsvFile(s, filePath, &record))
			}
		} else {
			log.Debugf("Logs already processed, ignoring (Id = %s)", record.Id)
		}
	}
	// NOTE: event log files come in cronological order, and thus the last one is also the most recent
	lastLogDate, err := time.Parse(LogDateFormat, lastLogDateStr)
	if err != nil {
		log.Warnf("Error parsing the last EventLogFile LogDate")
		// Fallback to now
		lastLogDate = time.Now()
	}
	return csvFiles, lastLogDate
}

func buildCsvFile(s SalesforceReceiverInterface, filePath string, record *query.EventLogfileRecord) CsvFile {
	// Get field mapping for curret event type
	// NOTE: viper's mapstructure lowercases all map keys: https://github.com/spf13/viper/issues/373
	fields, eventFound := s.getConfig().FieldMapping[strings.ToLower(record.EventType)]
	if !eventFound {
		fields = []string{}
	}
	// Generate field mapping
	fieldMapping := FieldMapping{}
	for _, field := range fields {
		fieldMapping[field] = true
	}
	// Add log record Id to cache
	addToCache(s, record.Id)

	return CsvFile{filePath, record.EventType, fieldMapping}
}

func parseCsvFile(csvFile CsvFile) (*CsvContext, error) {
	file, err := os.Open(csvFile.FilePath)
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

func logIdCacheKey(s SalesforceReceiverInterface, id string) string {
	return s.getConfig().Name + "_" + id
}

// Check if log ID is present in the cache (was already sent)
func notCached(s SalesforceReceiverInterface, id string) bool {
	val, err := s.getDB().GetCacheVal(logIdCacheKey(s, id))
	if err != nil {
		log.Warnf("Error accessing the cache: %s", err.Error())
		return true
	}
	return val == nil
}

func addToCache(s SalesforceReceiverInterface, id string) {
	err := s.getDB().SetCacheVal(logIdCacheKey(s, id), 1)
	if err != nil {
		log.Warnf("Error setting log Id in the cache: %s", err.Error())
	}
}

func processEventResponse(s SalesforceReceiverInterface, response *query.GenericEventResponse, sender DataSenderInterface, customQuery *config.QueryConfig) {
	totalEventsSent := 0
	dedupWarningWasShown := false

	for _, record := range response.Records {
		id, idPresent := record["Id"].(string)
		if !idPresent {
			id = buildCustomId(record, customQuery)
			idPresent = (id != "")
		}
		if idPresent {
			// De-duplicate event
			if notCached(s, id) {
				data := sender.buildCustom(record, customQuery.Timestamp)
				sender.send(data)
				addToCache(s, id)
				totalEventsSent += 1
			} else {
				log.Debugf("Event already processed, ignoring (Id = %s)", id)
			}
		} else {
			if !dedupWarningWasShown {
				log.Warnf("Events of type '%s' do not have an 'Id' field nor defines a custom id field, can't de-duplicate. Check the 'select' field for the correspondig 'soql' query in the 'customQueries' config.", customQuery.Soql.From)
				dedupWarningWasShown = true
			}

			data := sender.buildCustom(record, customQuery.Timestamp)
			sender.send(data)
			totalEventsSent += 1
		}
	}

	log.Debugf("Total events sent = %d", totalEventsSent)
}

func buildCustomId(record map[string]any, customQuery *config.QueryConfig) string {
	if len(customQuery.CustomId) > 0 {
		hashVal := sha256.New()
		for _, fieldName := range customQuery.CustomId {
			fieldVal, ok := record[fieldName]
			if !ok {
				log.Warnf("Custom ID field '%s' is not present in the event of type '%s'.", fieldName, customQuery.Soql.From)
				return ""
			}
			hashVal.Write([]byte(fmt.Sprintf("%v", fieldVal)))
		}
		return hex.EncodeToString(hashVal.Sum(nil))
	} else {
		return ""
	}
}

func processLimitsResponse(response map[string]query.SingleLimitResponse, sender DataSenderInterface) {
	for name, limit := range response {
		data := sender.buildLimit(name, limit)
		sender.send(data)
	}
}

func NewSalesforceEventsReceiver(i *integration.LabsIntegration, instanceConfig *config.EventLogConfig, db cache.Cache) pipeline.EventsReceiver {
	return &SalesforceEventsReceiver{
		i:              i,
		instanceConfig: instanceConfig,
		db:             db,
	}
}

func NewSalesforceLogsReceiver(i *integration.LabsIntegration, instanceConfig *config.EventLogConfig, db cache.Cache) pipeline.LogsReceiver {
	return &SalesforceLogsReceiver{
		i:              i,
		instanceConfig: instanceConfig,
		db:             db,
	}
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
