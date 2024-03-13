from requests import Session

from newrelic_logging.config import Config


class QueryStub:
    def __init__(self, config: dict):
        self.config = Config(config)

    def get(self, key: str, default = None):
        return self.config.get(key, default)

    def get_config(self):
        return self.config

    def execute():
        pass


class ResponseStub:
    def __init__(self, status_code, reason, text, lines):
        self.status_code = status_code
        self.reason = reason
        self.text = text
        self.lines = lines

    def iter_lines(self, *args, **kwargs):
        yield from self.lines


class SessionStub:
    def __init__(self, lines):
        self.response = None

    def get(self, *args, **kwargs):
        return self.response


class DataCacheStub:
    def __init__(
        self,
        cached_logs = {},
        cached_events = [],
        skip_record_ids = [],
        cached_log_lines = {},
    ):
        self.cached_logs = cached_logs
        self.cached_events = cached_events
        self.skip_record_ids = skip_record_ids
        self.cached_log_lines = cached_log_lines
        self.flush_called = False

    def can_skip_downloading_logfile(self, record_id: str) -> bool:
        return record_id in self.skip_record_ids

    def load_cached_log_lines(self, record_id: str) -> None:
        if record_id in self.cached_log_lines:
            self.cached_logs[record_id] = self.cached_log_lines[record_id]

    def check_and_set_log_line(self, record_id: str, row: dict) -> bool:
        return record_id in self.cached_logs and \
            row['REQUEST_ID'] in self.cached_logs[record_id]

    def check_and_set_event_id(self, record_id: str) -> bool:
        return record_id in self.cached_events

    def flush(self) -> None:
        self.flush_called = True


class NewRelicStub:
    def __init__(self):
        self.logs = []
        self.events = []

    def post_logs(self, session: Session, data: list[dict]) -> None:
        self.logs.append(data)

    def post_events(self, session: Session, events: list[dict]) -> None:
        self.events.append(events)
