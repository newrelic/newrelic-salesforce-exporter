import gzip
import json
from requests import RequestException, Session

from . import \
    VERSION, \
    NAME, \
    PROVIDER, \
    COLLECTOR_NAME, \
    NewRelicApiException
from .config import Config


NR_LICENSE_KEY = 'NR_LICENSE_KEY'
NR_ACCOUNT_ID = 'NR_ACCOUNT_ID'

US_LOGGING_ENDPOINT = 'https://log-api.newrelic.com/log/v1'
EU_LOGGING_ENDPOINT = 'https://log-api.eu.newrelic.com/log/v1'
LOGS_EVENT_SOURCE = 'logs'

US_EVENTS_ENDPOINT = 'https://insights-collector.newrelic.com/v1/accounts/{account_id}/events'
EU_EVENTS_ENDPOINT = 'https://insights-collector.eu01.nr-data.net/v1/accounts/{account_id}/events'

CONTENT_ENCODING = 'gzip'
MAX_EVENTS = 2000


class NewRelic:
    def __init__(
        self,
        logs_api_endpoint,
        logs_license_key,
        events_api_endpoint,
        events_api_key,
    ):
        self.logs_api_endpoint = logs_api_endpoint
        self.logs_license_key = logs_license_key
        self.events_api_endpoint = events_api_endpoint
        self.events_api_key = events_api_key

    def post_logs(self, session: Session, data: list[dict]) -> None:
        # Append integration attributes
        for log in data[0]['logs']:
            if not 'attributes' in log:
                log['attributes'] = {}
            log['attributes']['instrumentation.name'] = NAME
            log['attributes']['instrumentation.provider'] = PROVIDER
            log['attributes']['instrumentation.version'] = VERSION
            log['attributes']['collector.name'] = COLLECTOR_NAME

        try:
            r = session.post(
                self.logs_api_endpoint,
                data=gzip.compress(json.dumps(data).encode()),
                headers={
                    'X-License-Key': self.logs_license_key,
                    'X-Event-Source': LOGS_EVENT_SOURCE,
                    'Content-Encoding': CONTENT_ENCODING,
                },
            )

            if r.status_code != 202:
                raise NewRelicApiException(
                    f'newrelic logs api returned code {r.status_code}'
                )

            response = r.content.decode("utf-8")
        except RequestException:
            raise NewRelicApiException('newrelic logs api request failed')

    def post_events(self, session: Session, events: list[dict]) -> None:
        # Append integration attributes
        for event in events:
            event['instrumentation.name'] = NAME
            event['instrumentation.provider'] = PROVIDER
            event['instrumentation.version'] = VERSION
            event['collector.name'] = COLLECTOR_NAME

        # This funky code produces an array of arrays where each one will be at most
        # length 2000 with the last one being <= 2000. This is done to account for
        # the fact that only 2000 events can be posted at a time.

        slices = [events[i:(i + MAX_EVENTS)] \
            for i in range(0, len(events), MAX_EVENTS)]

        for slice in slices:
            try:
                r = session.post(
                    self.events_api_endpoint,
                    data=gzip.compress(json.dumps(slice).encode()),
                    headers={
                        'Api-Key': self.events_api_key,
                        'Content-Encoding': CONTENT_ENCODING,
                    },
                )

                if r.status_code != 200:
                    raise NewRelicApiException(
                        f'newrelic events api returned code {r.status_code}'
                    )

                response = r.content.decode("utf-8")
            except RequestException:
                raise NewRelicApiException('newrelic events api request failed')


def new_new_relic(config: Config):
    license_key = config.get(
        'newrelic.license_key',
        env_var_name=NR_LICENSE_KEY,
    )

    region = config.get('newrelic.api_endpoint')
    account_id = config.get('newrelic.account_id', env_var_name=NR_ACCOUNT_ID)

    if region == "US":
        logs_api_endpoint = US_LOGGING_ENDPOINT
        events_api_endpoint = US_EVENTS_ENDPOINT.format(account_id=account_id)
    elif region == "EU":
        logs_api_endpoint = EU_LOGGING_ENDPOINT
        events_api_endpoint = EU_EVENTS_ENDPOINT.format(account_id=account_id)
    else:
        raise NewRelicApiException(f'Invalid region {region}')

    return NewRelic(
        logs_api_endpoint,
        license_key,
        events_api_endpoint,
        license_key,
    )
