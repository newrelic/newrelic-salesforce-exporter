import gzip
import json
from .telemetry import Telemetry
from requests import RequestException

class NewRelicApiException(Exception):
    pass

class NewRelic:
    INGEST_SERVICE_VERSION = "v1"
    US_LOGGING_ENDPOINT = "https://log-api.newrelic.com/log/v1"
    EU_LOGGING_ENDPOINT = "https://log-api.eu.newrelic.com/log/v1"
    LOGS_EVENT_SOURCE = 'logs'

    US_EVENTS_ENDPOINT = "https://insights-collector.newrelic.com/v1/accounts/{account_id}/events"
    EU_EVENTS_ENDPOINT = "https://insights-collector.eu01.nr-data.net/v1/accounts/{account_id}/events"

    CONTENT_ENCODING = 'gzip'

    logs_api_endpoint = US_LOGGING_ENDPOINT
    logs_license_key = ''

    events_api_endpoint = US_EVENTS_ENDPOINT
    events_api_key = ''

    @classmethod
    def post_logs(cls, session, data):
        json_payload = json.dumps(data).encode()
        
        # print("----- POST DATA (LOGS) -----")
        # print(json_payload.decode("utf-8"))
        # print("----------------------------")
        # return 202

        payload = gzip.compress(json_payload)
        headers = {
            "X-License-Key": cls.logs_license_key,
            "X-Event-Source": cls.LOGS_EVENT_SOURCE,
            "Content-Encoding": cls.CONTENT_ENCODING,
        }
        try:
            r = session.post(cls.logs_api_endpoint, data=payload,
                             headers=headers)
        except RequestException as e:
            Telemetry().log_err(f"Failed posting logs to New Relic: {repr(e)}")
            return 0
        
        print("NR Log API response body = ", r.content.decode("utf-8"))

        return r.status_code

    @classmethod
    def post_events(cls, session, data):
        json_payload = json.dumps(data).encode()

        # print("----- POST DATA (EVENTS) -----")
        # print(json_payload.decode("utf-8"))
        # print("------------------------------")
        # return 200

        payload = gzip.compress(json_payload)
        headers = {
            "Api-Key": cls.events_api_key,
            "Content-Encoding": cls.CONTENT_ENCODING,
        }
        try:
            r = session.post(cls.events_api_endpoint, data=payload,
                             headers=headers)
        except RequestException as e:
            Telemetry().log_err(f"Failed posting events to New Relic: {repr(e)}")
            return 0
        
        print("NR Event API response body = ", r.content.decode("utf-8"))

        return r.status_code

    @classmethod
    def set_api_endpoint(cls, api_endpoint, account_id):
        if api_endpoint == "US":
            api_endpoint = NewRelic.US_EVENTS_ENDPOINT;
        elif api_endpoint == "EU":
            api_endpoint = NewRelic.EU_EVENTS_ENDPOINT
        NewRelic.events_api_endpoint = api_endpoint.format(account_id='account_id')

    @classmethod
    def set_logs_endpoint(cls, api_endpoint):
        if api_endpoint == "US":
            NewRelic.logs_api_endpoint = NewRelic.US_LOGGING_ENDPOINT
        elif api_endpoint == "EU":
            NewRelic.logs_api_endpoint = NewRelic.EU_LOGGING_ENDPOINT
        else:
            NewRelic.logs_api_endpoint = api_endpoint
