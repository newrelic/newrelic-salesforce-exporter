import gzip
import json

from requests import RequestException


class NewRelicApiException(Exception):
    pass


class NewRelic:
    INGEST_SERVICE_VERSION = "v1"
    US_LOGGING_ENDPOINT = "https://log-api.newrelic.com/log/v1"
    EU_LOGGING_ENDPOINT = "https://log-api.eu.newrelic.com/log/v1"
    EVENT_SOURCE = 'logs'
    CONTENT_ENCODING = 'gzip'

    api_endpoint = US_LOGGING_ENDPOINT
    license_key = ''

    @classmethod
    def post(cls, session, data):
        payload = gzip.compress(json.dumps(data).encode())
        headers = {
            "X-License-Key": cls.license_key,
            "X-Event-Source": cls.EVENT_SOURCE,
            "Content-Encoding": cls.CONTENT_ENCODING,
        }
        try:
            r = session.post(cls.api_endpoint, data=payload,
                             headers=headers)
        except RequestException as e:
            raise NewRelicApiException(repr(e)) from e
        return r.status_code
