from enum import Enum
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

US_LOGS_ENDPOINT = 'https://log-api.newrelic.com/log/v1'
EU_LOGS_ENDPOINT = 'https://log-api.eu.newrelic.com/log/v1'
FEDRAMP_LOGS_ENDPOINT = 'https://gov-log-api.newrelic.com/log/v1'
LOGS_EVENT_SOURCE = 'logs'

US_EVENTS_ENDPOINT = 'https://insights-collector.newrelic.com/v1/accounts/{account_id}/events'
EU_EVENTS_ENDPOINT = 'https://insights-collector.eu01.nr-data.net/v1/accounts/{account_id}/events'
FEDRAMP_EVENTS_ENDPOINT = 'https://gov-insights-collector.newrelic.com/v1/accounts/{account_id}/events'

CONTENT_ENCODING = 'gzip'
MAX_EVENTS = 2000


class Region(Enum):
    US = 'US'
    EU = 'EU'
    FEDRAMP = 'FEDRAMP'


def get_region(region: str) -> Region:
    region_u = region.upper()

    if region_u == Region.US.value:
        return Region.US

    if region_u == Region.EU.value:
        return Region.EU

    if region_u == Region.FEDRAMP.value:
        return Region.FEDRAMP

    raise NewRelicApiException(f'invalid New Relic API region {region}')


def get_logs_endpoint(region: str) -> str:
    r = get_region(region)

    if r == Region.EU:
        return EU_LOGS_ENDPOINT

    if r == Region.FEDRAMP:
        return FEDRAMP_LOGS_ENDPOINT

    # Since get_region() either returns a valid Region or raises an exception,
    # the only other possible value is Region.US so return the US logs endpoint.

    return US_LOGS_ENDPOINT


def get_events_endpoint(region: str, account_id: str) -> str:
    r = get_region(region)

    if r == Region.EU:
        return EU_EVENTS_ENDPOINT.format(account_id=account_id)

    if r == Region.FEDRAMP:
        return FEDRAMP_EVENTS_ENDPOINT.format(account_id=account_id)

    # Since get_region() either returns a valid Region or raises an exception,
    # the only other possible value is Region.US so return the US events
    # endpoint.

    return US_EVENTS_ENDPOINT.format(account_id=account_id)


class NewRelic:
    def __init__(
        self,
        license_key,
        logs_api_endpoint,
        events_api_endpoint
    ):
        self.license_key = license_key
        self.logs_api_endpoint = logs_api_endpoint
        self.events_api_endpoint = events_api_endpoint

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
                    'X-License-Key': self.license_key,
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
                        'Api-Key': self.license_key,
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
