from requests import RequestException, Session, Response
from typing import Any

from . import SalesforceApiException
from .auth import Authenticator
from .telemetry import print_warn

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


class Api:
    def __init__(self, authenticator: Authenticator, api_ver: str):
        self.authenticator = authenticator
        self.api_ver = api_ver

    def authenticate(self, session: Session) -> None:
        self.authenticator.authenticate(session)

    def query(self, session: Session, soql: str, api_ver: str = None) -> dict:
        ver = self.api_ver
        if not api_ver is None:
            ver = api_ver

        return get(
            self.authenticator,
            session,
            f'/services/data/v{ver}/query?q={soql}',
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

class ApiFactory:
    def __init__(self):
        pass

    def new(self, authenticator: Authenticator, api_ver: str) -> Api:
        return Api(authenticator, api_ver)
