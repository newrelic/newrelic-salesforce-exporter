import gc
from requests import Session

from . import DataFormat
from .cache import DataCache
from .config import Config
from .http_session import new_retry_session
from .newrelic import NewRelic
from .telemetry import print_info
from .util import maybe_convert_str_to_num


DEFAULT_MAX_ROWS = 1000
MAX_ROWS = 2000


def load_as_logs(
    iter,
    new_relic: NewRelic,
    labels: dict,
    max_rows: int,
) -> None:
    nr_session = new_retry_session()

    logs = []
    count = total = 0

    def send_logs():
        nonlocal logs
        nonlocal count

        new_relic.post_logs(nr_session, [{'common': labels, 'logs': logs}])

        print_info(f'Sent {count} log messages.')

        # Attempt to release memory
        del logs

        logs = []
        count = 0

    for log in iter:
        if count == max_rows:
            send_logs()

        logs.append(log)

        count += 1
        total += 1

    if len(logs) > 0:
        send_logs()

    print_info(f'Sent a total of {total} log messages.')

    # Attempt to reclaim memory
    gc.collect()


def pack_log_into_event(
    log: dict,
    labels: dict,
    numeric_fields_list: set,
) -> dict:
    log_event = {}

    attributes = log['attributes']
    for key in attributes:
        value = attributes[key]

        if key in numeric_fields_list:
            log_event[key] = \
                maybe_convert_str_to_num(value) if value \
                else 0
            continue

        log_event[key] = value

    log_event.update(labels)
    log_event['eventType'] = log_event.get('EVENT_TYPE', "UnknownSFEvent")

    return log_event


def load_as_events(
    iter,
    new_relic: NewRelic,
    labels: dict,
    max_rows: int,
    numeric_fields_list: set,
) -> None:
    nr_session = new_retry_session()

    events = []
    count = total = 0

    def send_events():
        nonlocal events
        nonlocal count

        new_relic.post_events(nr_session, events)

        print_info(f'Sent {count} events.')

        # Attempt to release memory
        del events

        events = []
        count = 0


    for log_entry in iter:
        if count == max_rows:
            send_events()

        events.append(pack_log_into_event(
            log_entry,
            labels,
            numeric_fields_list,
        ))

        count += 1
        total += 1

    if len(events) > 0:
        send_events()

    print_info(f'Sent a total of {total} events.')

    # Attempt to reclaim memory
    gc.collect()


def load_data(
    logs,
    new_relic: NewRelic,
    data_format: DataFormat,
    labels: dict,
    max_rows: int,
    numeric_fields_list: set,
):
    if data_format == DataFormat.LOGS:
        load_as_logs(
            logs,
            new_relic,
            labels,
            max_rows,
        )
        return

    load_as_events(
        logs,
        new_relic,
        labels,
        max_rows,
        numeric_fields_list,
    )


class Pipeline:
    def __init__(
        self,
        config: Config,
        data_cache: DataCache,
        new_relic: NewRelic,
        data_format: DataFormat,
        labels: dict,
        numeric_fields_list: set,
    ):
        self.config = config
        self.data_cache = data_cache
        self.new_relic = new_relic
        self.data_format = data_format
        self.labels = labels
        self.numeric_fields_list = numeric_fields_list
        self.max_rows = min(
            self.config.get('max_rows', DEFAULT_MAX_ROWS),
            MAX_ROWS,
        )
        self.receivers = []

    def add_receiver(self, receiver) -> None:
        self.receivers.append(receiver)

    def yield_all(
        self,
        session: Session,
    ):
        for receiver in self.receivers:
            yield from receiver.execute(session)

    def execute(
        self,
        session: Session,
    ):
        load_data(
            self.yield_all(session),
            self.new_relic,
            self.data_format,
            self.labels,
            self.max_rows,
            self.numeric_fields_list,
        )
