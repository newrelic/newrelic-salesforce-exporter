package query

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"runtime"
	"time"

	"github.com/newrelic/newrelic-labs-sdk/v2/pkg/integration/log"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/cache"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/config"
	"github.com/newrelic/newrelic-salesforce-exporter/internal/oauth"
)

const (
	defaultTimeout = 5 * time.Second
)

// TODO: Support other auth flows:
// (alreadys upported) Username-Password: https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_username_password_flow.htm&type=5
// JWT: https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_jwt_flow.htm&type=5
// Client credentials: https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_oauth_client_credentials_flow.htm&type=5
// Only JWT supports token refresh

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

func RequestLogFiles(conf *config.EventLogInstance, db cache.Cache, since time.Time, until time.Time) (EventLogfileResponse, error) {
	soqlModel := MakeSoqlQuery("EventLogFile", "Id", "EventType", "LogDate", "LogFile")
	soqlModel.AndWhere("Interval = 'Hourly'")
	soqlModel.AndWhere("LogDate >= " + since.UTC().Format(time.RFC3339))
	soqlModel.AndWhere("LogDate <= " + until.UTC().Format(time.RFC3339))
	// Apply EventType filter
	if len(conf.EventTypes) > 0 {
		eventTypeFilter := make([]string, 0)
		for _, eventType := range conf.EventTypes {
			eventTypeFilter = append(eventTypeFilter, "EventType" + " = " + "'" + eventType + "'")
		}
		soqlModel.AndOrWhere(eventTypeFilter...)
	}
	soql := soqlModel.Build()
	
	log.Debugf("Run SOQL query: %s", soql)
	
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

func DownloadCsvFile(conf *config.EventLogInstance, db cache.Cache, record *EventLogfileRecord) (string, error) {
	resp, err := request(conf, db, conf.Auth.TokenUrl + record.LogFile, false)
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
	req.Header.Add("Authorization", "Bearer " + accessToken)

	client := http.DefaultClient
	client.Timeout = defaultTimeout

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
	return "/tmp/" + record.Id + ".csv"
}