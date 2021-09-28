import requests
from requests.adapters import HTTPAdapter, Retry

DEFAULT_TIMEOUT = 5  # seconds


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def new_retry_session(retries=3,
                      backoff_factor=3,
                      status_forcelist=(500, 502, 504),
                      session=None,
                      ):
    session = session or requests.Session()
    max_retries = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = TimeoutHTTPAdapter(max_retries=max_retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
