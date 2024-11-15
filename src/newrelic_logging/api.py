from requests import RequestException, Session, Response
from typing import Any

from . import SalesforceApiException
from .auth import Authenticator
from .telemetry import print_warn

API_NAME_REST = 'rest'
API_NAME_TOOLING = 'tooling'
DEFAULT_API_NAME = API_NAME_REST

def get(
    auth: Authenticator,
    session: Session,
    serviceUrl: str,
    cb,
    stream: bool = False,
) -> Any:
    url = f'{auth.get_instance_url()}{serviceUrl}'

    try:
        headers = {
            'Authorization': f'Bearer {auth.get_access_token()}'
        }

        response = session.get(url, headers=headers, stream=stream)

        status_code = response.status_code

        if status_code == 200:
            return cb(response)

        if status_code == 401:
            print_warn(
               f'invalid token while executing api operation: {url}',
            )
            auth.reauthenticate(session)

            new_headers = {
                'Authorization': f'Bearer {auth.get_access_token()}'
            }

            response = session.get(url, headers=new_headers, stream=stream)
            if response.status_code == 200:
                return cb(response)

        raise SalesforceApiException(
            status_code,
            f'error executing api operation: {url}, ' \
            f'status-code: {status_code}, ' \
            f'reason: {response.reason}, '
        )
    except ConnectionError as e:
        raise SalesforceApiException(
            -1,
            f'connection error executing api operation: {url}',
        ) from e
    except RequestException as e:
        raise SalesforceApiException(
            -1,
            f'request error executing api operation: {url}',
        ) from e


def stream_lines(response: Response, chunk_size: int):
    if response.encoding is None:
        response.encoding = 'utf-8'

    # Stream the response as a set of lines. This function will return an
    # iterator that yields one line at a time holding only the minimum
    # amount of data chunks in memory to make up a single line

    return response.iter_lines(
        decode_unicode=True,
        chunk_size=chunk_size,
    )


def get_query_api_path(api_ver: str, api_name: str) -> str:
    l_api_name = api_name.lower()

    if l_api_name == API_NAME_REST:
        return f'/services/data/v{api_ver}/query'

    if l_api_name == API_NAME_TOOLING:
        return f'/services/data/v{api_ver}/tooling/query'

    raise SalesforceApiException(
        -1,
        f'invalid query api name {api_name}',
    )


class Api:
    def __init__(self, authenticator: Authenticator, api_ver: str):
        self.authenticator = authenticator
        self.api_ver = api_ver

    def authenticate(self, session: Session) -> None:
        self.authenticator.authenticate(session)

    def query(
        self,
        session: Session,
        soql: str,
        api_ver: str = None,
        api_name: str = None,
    ) -> dict:
        ver = self.api_ver
        if not api_ver is None:
            ver = api_ver

        api = DEFAULT_API_NAME
        if not api_name is None:
            api = api_name

        url = get_query_api_path(ver, api)

        return get(
            self.authenticator,
            session,
            f'{url}?q={soql}',
            lambda response : response.json()
        )

    def query_more(
        self,
        session: Session,
        next_records_url: str,
    ) -> dict:
        return get(
            self.authenticator,
            session,
            next_records_url,
            lambda response : response.json()
        )

    def get_log_file(
        self,
        session: Session,
        log_file_path: str,
        chunk_size: int,
    ):
        return get(
            self.authenticator,
            session,
            log_file_path,
            lambda response : stream_lines(response, chunk_size),
            stream=True,
        )

    def list_limits(self, session: Session, api_ver: str = None) -> dict:
        ver = self.api_ver
        if not api_ver is None:
            ver = api_ver

        return get(
            self.authenticator,
            session,
            f'/services/data/v{ver}/limits/',
            lambda response : response.json(),
        )
