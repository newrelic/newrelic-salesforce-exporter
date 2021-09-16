import requests
import json
import gzip


class NewRelic:
    INGEST_SERVICE_VERSION = "v1"
    US_LOGGING_ENDPOINT = "https://log-api.newrelic.com/log/v1"
    EU_LOGGING_ENDPOINT = "https://log-api.eu.newrelic.com/log/v1"
    EVENT_SOURCE = 'logs'
    CONTENT_ENCODING = 'gzip'

    api_endpoint = US_LOGGING_ENDPOINT
    license_key = ''

    @classmethod
    def post(cls, data):
        payload = gzip.compress(json.dumps(data).encode())
        headers = {
            "X-License-Key": cls.license_key,
            "X-Event-Source": cls.EVENT_SOURCE,
            "Content-Encoding": cls.CONTENT_ENCODING,
        }
        r = requests.post(cls.api_endpoint, data=payload,
                          headers=headers)
        # print(f"newrelic_logging logs post returned code {r.status_code}")
        return r.status_code
