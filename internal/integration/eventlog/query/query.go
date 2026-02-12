package query

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"time"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/oauth"
)

func auth(conf *config.EventLogInstance, db cache.Cache) (string, error) {
	accessToken, ok := getTokenFromCache(conf, db).(string)
	if ok {
		log.Debugf("Got token from cache")
		return accessToken, nil
	} else {
		log.Debugf("No token in cache, send login request")
		login, err := oauth.Login(conf.Auth)
		if err != nil {
			return "", err
		}
		setTokenIntoCache(conf, db, login.AccessToken)
		return login.AccessToken, nil
	}
}

func relogin(conf *config.EventLogInstance, db cache.Cache) error {
	deleteTokenFromCache(conf, db)
	_, reqErr := auth(conf, db)
	if reqErr != nil {
		return reqErr
	}
	return nil
}

func getTokenFromCache(conf *config.EventLogInstance, db cache.Cache) any {
	val, err := db.GetCacheVal(tokenCacheKey(conf))
	if err != nil {
		log.Errorf("Error getting token from cache: %s", err.Error())
	}
	return val
}

func setTokenIntoCache(conf *config.EventLogInstance, db cache.Cache, accessToken string) {
	err := db.SetCacheVal(tokenCacheKey(conf), accessToken)
	if err != nil {
		log.Errorf("Error setting token into cache: %s", err.Error())
	}
}

func deleteTokenFromCache(conf *config.EventLogInstance, db cache.Cache) {
	err := db.DelCacheVal(tokenCacheKey(conf))
	if err != nil {
		log.Errorf("Error deleting token from cache: %s", err.Error())
	}
}

func tokenCacheKey(conf *config.EventLogInstance) string {
	return conf.Name + "_access_token"
}

// Request EventLogFile object.
// Result: List of log files. Each one being a relative path to download a CSV file.
func RequestLogFiles(conf *config.EventLogInstance, db cache.Cache, since time.Time, until time.Time) (EventLogfileResponse, error) {
	soqlModel := MakeSoqlQuery("EventLogFile", "Id", "EventType", "CreatedDate", "LogDate", "LogFile")
	soqlModel.AndWhere("Interval = 'Hourly'")
	soqlModel.AndWhere("CreatedDate >= " + since.UTC().Format(time.RFC3339))
	soqlModel.AndWhere("CreatedDate <= " + until.UTC().Format(time.RFC3339))
	// Apply EventType filter
	if len(conf.EventTypes) > 0 {
		eventTypeFilter := make([]string, 0)
		for _, eventType := range conf.EventTypes {
			eventTypeFilter = append(eventTypeFilter, "EventType"+" = "+"'"+eventType+"'")
		}
		soqlModel.AndOrWhere(eventTypeFilter...)
	}
	soql := soqlModel.Build()

	log.Debugf("Run EventLogFile SOQL query: %s", soql)

	url := conf.Auth.TokenUrl + "/services/data/v" + conf.ApiVer + "/query?q=" + soql

	resp, err := request(conf, db, url, false)
	if err != nil {
		return EventLogfileResponse{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
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
	} else {
		return EventLogfileResponse{}, fmt.Errorf("Unexpected status code %d", resp.StatusCode)
	}
}

// Download a CSV file to disk.
// Result: Local path to downloaded file.
func DownloadCsvFile(conf *config.EventLogInstance, db cache.Cache, record *EventLogfileRecord) (string, error) {
	resp, err := request(conf, db, conf.Auth.TokenUrl+record.LogFile, false)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
		filePath := csvFilePath(record)
		outFile, err := os.Create(filePath)
		if err != nil {
			return "", err
		}
		defer outFile.Close()

		_, err = io.Copy(outFile, resp.Body)

		return filePath, err
	} else {
		return "", fmt.Errorf("Unexpected status code %d", resp.StatusCode)
	}
}

// Send a SOQL request.
// Result: response object.
func RequestCustomQuery(customQuery *config.QueryConfig, conf *config.EventLogInstance, db cache.Cache, since time.Time, until time.Time) (GenericEventResponse, error) {
	soqlModel := MakeSoqlQuery(customQuery.Soql.From, customQuery.Soql.Select...)
	soqlModel.AndWhere(customQuery.Soql.Where)
	soqlModel.AndWhere(customQuery.Timestamp + " >= " + since.UTC().Format(time.RFC3339))
	soqlModel.AndWhere(customQuery.Timestamp + " <= " + until.UTC().Format(time.RFC3339))
	soqlModel.Tail(customQuery.Soql.Tail)
	soql := soqlModel.Build()

	log.Debugf("Run custom SOQL query: %s", soql)

	// Base URL
	url := conf.Auth.TokenUrl + "/services/data/v" + customQuery.ApiVer

	if customQuery.ApiName == "rest" {
		// REST API
		url += "/query"
	} else {
		// TOOLING API
		url += "/tooling/query"
	}

	// Add SOQL query
	url += "?q=" + soql

	resp, err := request(conf, db, url, false)
	if err != nil {
		return GenericEventResponse{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
		respBytes, err := io.ReadAll(resp.Body)
		if err != nil {
			return GenericEventResponse{}, err
		}

		var response GenericEventResponse
		err = json.Unmarshal(respBytes, &response)
		if err != nil {
			return GenericEventResponse{}, err
		}

		jresp, _ := json.MarshalIndent(response, "", "    ")
		log.Debugf("Query result:\n%s", string(jresp))

		return response, nil
	} else {
		return GenericEventResponse{}, fmt.Errorf("Unexpected status code %d", resp.StatusCode)
	}
}

// Request Salesforce Org limits
// Result: list of limits.
func RequestLimits(conf *config.EventLogInstance, db cache.Cache) (map[string]SingleLimitResponse, error) {
	limitsConf := &conf.Limits
	url := conf.Auth.TokenUrl + "/services/data/v" + limitsConf.ApiVer + "/limits"

	resp, err := request(conf, db, url, false)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
		respBytes, err := io.ReadAll(resp.Body)
		if err != nil {
			return nil, err
		}

		var response map[string]SingleLimitResponse
		err = json.Unmarshal(respBytes, &response)
		if err != nil {
			return nil, err
		}

		jresp, _ := json.MarshalIndent(response, "", "    ")
		log.Debugf("Query result:\n%s", string(jresp))

		if len(limitsConf.Names) == 0 {
			return response, nil
		} else {
			// Filter limits
			filteredResponse := map[string]SingleLimitResponse{}
			for _, limitName := range limitsConf.Names {
				limit, limitExists := response[limitName]
				if limitExists {
					filteredResponse[limitName] = limit
				}
			}
			return filteredResponse, nil
		}
	} else {
		return nil, fmt.Errorf("Unexpected status code %d", resp.StatusCode)
	}
}

// Perform a generic request to Salesforce API.
func request(conf *config.EventLogInstance, db cache.Cache, url string, isRetry bool) (*http.Response, error) {
	accessToken, err := auth(conf, db)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Add("User-Agent", getUserAgent())
	req.Header.Add("Authorization", "Bearer "+accessToken)

	client := http.DefaultClient
	client.Timeout = time.Duration(conf.RequestTimeout) * time.Second

	resp, err := client.Do(req)

	if err == nil {
		if resp.StatusCode == 401 && !isRetry {
			log.Warnf("Wrong credentials error (401). Try relogging...")
			err := relogin(conf, db)
			if err != nil {
				return nil, err
			}
			// Retry request after relogin
			return request(conf, db, url, true)
		} else {
			return resp, nil
		}
	} else {
		return nil, err
	}
}

func getUserAgent() string {
	return fmt.Sprintf(
		"nr-salesforce-eventlog (%s; %s)",
		runtime.GOOS,
		runtime.GOARCH,
	)
}

func csvFilePath(record *EventLogfileRecord) string {
	return filepath.Join(os.TempDir(), record.Id+".csv")
}
