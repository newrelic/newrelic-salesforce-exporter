package query

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"runtime"
	"time"

	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
)

const (
	defaultTimeout = 5 * time.Second
)

type ReloginError struct {}

func (e *ReloginError) Error() string {
    return "Relogin error (401)"
}

func IsReloginError(e error) bool {
	_, ok := e.(*ReloginError)
	return ok
}

func RequestLogFiles(conf *config.EventLogInstance, token string, since time.Time, until time.Time) (EventLogfileResponse, error) {
	soqlModel := MakeSoqlQuery("EventLogFile", "Id", "EventType", "LogDate", "LogFile")
	soqlModel.AndWhere("Interval = 'Hourly'")
	soqlModel.AndWhere("LogDate >= " + since.UTC().Format(time.RFC3339))
	soqlModel.AndWhere("LogDate <= " + until.UTC().Format(time.RFC3339))
	soql := soqlModel.Build()

	url := conf.Auth.TokenUrl + "/services/data/v" + conf.ApiVer + "/query?q=" + soql

	resp, err := request(url, token)
	if err != nil {
		return EventLogfileResponse{}, err
	}
	defer resp.Body.Close()

	switch resp.StatusCode {
	case 200:
		respBytes, err := io.ReadAll(resp.Body)
		if err != nil {
			return EventLogfileResponse{}, err
		}

		var response EventLogfileResponse
		err = json.Unmarshal(respBytes, &response)
		if err != nil {
			return EventLogfileResponse{}, err
		}

		return response, nil
	case 401:
		return EventLogfileResponse{}, &ReloginError{}
	default:
		return EventLogfileResponse{}, err
	}
}

//TODO: log file API request
func RequestCsvFile() {

}

func request(url string, token string) (*http.Response, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Add("User-Agent", getUserAgent())
	req.Header.Add("Authorization", "Bearer " + token)

	client := http.DefaultClient
	client.Timeout = defaultTimeout

	return client.Do(req)
}

func getUserAgent() string {
	return fmt.Sprintf(
		"nr-salesforce-eventlog (%s; %s)",
		runtime.GOOS,
		runtime.GOARCH,
	)
}