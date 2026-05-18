package eventlog

import (
	"path/filepath"
	"reflect"
	"runtime"
	"strings"
	"testing"
	"time"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/integration/eventlog/query"
)

const LoginEventType = "Login"
const TestData = "/testdata/login_logs_sample.csv"
const UriField = "URI"
const RunTimeField = "RUN_TIME"

type SalesforceReceiverTest struct {
	db           cache.DummyCache
	instanceConf config.EventLogConfig
}

func NewSalesforceReceiverTest() SalesforceReceiverTest {
	return SalesforceReceiverTest{
		db: cache.DummyCache{},
		instanceConf: config.EventLogConfig{
			FieldMapping: config.FieldMappingConfig{
				//NOTE: viper's mapstructure lowercases map keys
				strings.ToLower(LoginEventType): config.FieldNames{UriField, RunTimeField},
			},
		},
	}
}

func (s *SalesforceReceiverTest) getConfig() *config.EventLogConfig {
	return &s.instanceConf
}

func (s *SalesforceReceiverTest) getDB() cache.Cache {
	return &s.db
}

func TestEventLogPipeline(t *testing.T) {
	_, filename, _, _ := runtime.Caller(0)
	testCsvPath := filepath.Dir(filename) + TestData

	s := NewSalesforceReceiverTest()
	record := query.EventLogfileRecord{
		EventType: LoginEventType,
	}

	// Build CSV file
	csvFile := buildCsvFile(&s, testCsvPath, &record)
	if csvFile.EventType != LoginEventType {
		t.Fatalf("EventType should be '%s', but is '%s'", LoginEventType, csvFile.EventType)
	}
	if csvFile.FilePath != testCsvPath {
		t.Fatalf("FilePath should be '%s', but is '%s'", testCsvPath, csvFile.FilePath)
	}
	fileMapping := FieldMapping{
		UriField:     true,
		RunTimeField: true,
	}
	if !reflect.DeepEqual(csvFile.FieldMapping, fileMapping) {
		t.Fatalf("Unexpected field mapping: %v", csvFile.FieldMapping)
	}

	// Parse CSV file
	csvContext, err := parseCsvFile(csvFile)
	if err != nil {
		t.Fatalf("Error parsing CSV: %s", err)
	}
	if csvContext.DidFinish {
		t.Fatalf("Did finish is true")
	}
	loginLabels := []string{
		"EVENT_TYPE", "TIMESTAMP", "REQUEST_ID", "ORGANIZATION_ID", "USER_ID",
		"RUN_TIME", "CPU_TIME", "URI", "SESSION_KEY", "LOGIN_KEY", "USER_TYPE",
		"REQUEST_STATUS", "DB_TOTAL_TIME", "LOGIN_TYPE", "BROWSER_TYPE", "API_TYPE",
		"API_VERSION", "USER_NAME", "TLS_PROTOCOL", "CIPHER_SUITE", "USE_API_TOKEN",
		"HTTP_REFERER", "LOGIN_URL", "COUNTRY_CODE",
		"AUTHENTICATION_METHOD_REFERENCE", "LOGIN_SUB_TYPE",
		"AUTHENTICATION_SERVICE_ID", "TIMESTAMP_DERIVED", "USER_ID_DERIVED",
		"CLIENT_IP", "URI_ID_DERIVED", "LOGIN_STATUS", "SOURCE_IP",
		"FORWARDED_FOR_IP",
	}
	if !reflect.DeepEqual(csvContext.Labels, loginLabels) {
		t.Fatalf("Unexpected labels: %v", csvContext.Labels)
	}
	if len(csvContext.Lines) != 0 {
		t.Fatalf("Unexpected empty lines: %v", csvContext.Lines)
	}

	// Read CSV data
	csvContext, err = readCsvData(csvContext)
	if err != nil {
		t.Fatalf("Error reading CSV lines: %s", err)
	}
	if len(csvContext.Lines) != 9 {
		t.Fatalf("CSV context should contain %d lines, but has %d", 9, len(csvContext.Lines))
	}

	// Build log line from CSV data
	data := buildCsvLineData(csvContext.Labels, csvContext.Lines[0], csvFile.FieldMapping)
	//t.Logf("Data generated:\n%+v", data)
	if data.text != "SFDC"+LoginEventType {
		t.Fatalf("Unexpected GenericSample text: %s", data.text)
	}
	expectedAttr := map[string]any{
		UriField:     "/services/oauth2/token",
		RunTimeField: 157,
	}
	if !reflect.DeepEqual(data.attributes, expectedAttr) {
		t.Fatalf("Unexpected GenericSample attributes: %+v", data.attributes)
	}
	expectedTs := time.Date(2025, 10, 01, 11, 00, 03, 509*1_000_000, time.UTC)
	if data.timestamp != expectedTs {
		t.Fatalf("Unexpected GenericSample timeseatmp: %+v", data.timestamp)
	}
}
