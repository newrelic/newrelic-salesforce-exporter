from copy import deepcopy
from requests import Session


from ..api import Api
from ..config import Config
from ..telemetry import print_info, print_warn
from ..util import \
    get_iso_date_with_offset, \
    substitute


def is_valid_records_response(response: dict) -> bool:
    return response is not None and \
        'records' in response and \
        isinstance(response['records'], list)


def has_more_records(response: dict) -> bool:
    return 'done' in response and \
        'nextRecordsUrl' in response and \
        not response['done'] and \
        not response['nextRecordsUrl'] == ''


class Query:
    def __init__(
        self,
        api: Api,
        query: str,
        options: Config,
        api_ver: str = None,
        api_name: str = None,
    ):
        self.api = api
        self.query = query
        self.options = options
        self.api_ver = api_ver
        self.api_name = api_name

    def get(self, key: str, default = None):
        return self.options.get(key, default)

    def get_config(self):
        return self.options

    def execute(
        self,
        session: Session,
    ):
        print_info(f'Running query {self.query}...')
        response = self.api.query(
            session,
            self.query,
            self.api_ver,
            self.api_name,
        )

        if not is_valid_records_response(response):
            print_warn(f'no records returned for query {self.query}')
            return

        done = False
        while not done:
            yield from response['records']

            if not has_more_records(response):
                done = True
                continue

            next_records_url = response['nextRecordsUrl']

            print_info(
                f'Retrieving more query results using {next_records_url}...'
            )

            response = self.api.query_more(
                session,
                next_records_url,
            )

            if not is_valid_records_response(response):
                print_warn(
                    f'no records returned for next records URL {next_records_url}'
                )
                done = True


class QueryFactory:
    def __init__(self):
        pass

    def build_args(
        self,
        time_lag_minutes: int,
        last_to_timestamp: str,
        generation_interval: str,
    ):
        return {
            'to_timestamp': get_iso_date_with_offset(time_lag_minutes),
            'from_timestamp': last_to_timestamp,
            'log_interval_type': generation_interval,
        }

    def get_env(self, q: dict) -> dict:
        if 'env' in q and type(q['env']) is dict:
            return q['env']

        return {}

    def new(
        self,
        api: Api,
        q: dict,
        time_lag_minutes: int,
        last_to_timestamp: str,
        generation_interval: str,
    ) -> Query:
        qp = deepcopy(q)
        qq = qp.pop('query', '')

        return Query(
            api,
            substitute(
                self.build_args(
                    time_lag_minutes,
                    last_to_timestamp,
                    generation_interval,
                ),
                qq,
                self.get_env(qp),
            ).replace(' ', '+'),
            Config(qp),
            qp.get('api_ver', None),
            qp.get('api_name', None),
        )
