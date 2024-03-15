from copy import deepcopy
import csv
from datetime import datetime
import gc
import pytz
from requests import Session

from . import DataFormat, SalesforceApiException
from .cache import DataCache
from .config import Config
from .http_session import new_retry_session
from .newrelic import NewRelic
from .query import Query
from .telemetry import print_info
from .util import generate_record_id, \
    is_logfile_response, \
    maybe_convert_str_to_num


DEFAULT_CHUNK_SIZE = 4096
DEFAULT_MAX_ROWS = 1000
MAX_ROWS = 2000

def init_fields_from_log_line(
    record_event_type: str,
    log_line: dict,
    event_type_fields_mapping: dict,
) -> dict:
    if record_event_type in event_type_fields_mapping:
        attrs = {}

        for field in event_type_fields_mapping[record_event_type]:
            attrs[field] = log_line[field]

        return attrs

    return deepcopy(log_line)


def get_log_line_timestamp(log_line: dict) -> float:
    epoch = log_line.get('TIMESTAMP')

    if epoch:
        return pytz.utc.localize(
            datetime.strptime(epoch, '%Y%m%d%H%M%S.%f')
        ).replace(microsecond=0).timestamp()

    return datetime.utcnow().replace(microsecond=0).timestamp()


def pack_log_line_into_log(
    query: Query,
    record_id: str,
    record_event_type: str,
    log_line: dict,
    line_no: int,
    event_type_fields_mapping: dict,
) -> dict:
    attrs = init_fields_from_log_line(
        record_event_type,
        log_line,
        event_type_fields_mapping,
    )

    timestamp = int(get_log_line_timestamp(log_line))
    attrs.pop('TIMESTAMP', None)

    attrs['LogFileId'] = record_id

    actual_event_type = attrs.pop('EVENT_TYPE', 'SFEvent')
    new_event_type = query.get('event_type', actual_event_type)
    attrs['EVENT_TYPE'] = new_event_type

    timestamp_field_name = query.get('rename_timestamp', 'timestamp')
    attrs[timestamp_field_name] = timestamp

    log_entry = {
        'message': f'LogFile {record_id} row {str(line_no)}',
        'attributes': attrs
    }

    if timestamp_field_name == 'timestamp':
        log_entry[timestamp_field_name] = timestamp

    return log_entry


def export_log_lines(
    session: Session,
    url: str,
    access_token: str,
    chunk_size: int,
):
    print_info(f'Downloading log lines for log file: {url}')

    # Request the log lines for the log file record url
    response = session.get(
        url,
        headers={
            'Authorization': f'Bearer {access_token}'
        },
        stream=True,
    )
    if response.status_code != 200:
        error_message = f'salesforce event log file download failed. ' \
                        f'status-code: {response.status_code}, ' \
                        f'reason: {response.reason} ' \
                        f'response: {response.text}'
        raise SalesforceApiException(response.status_code, error_message)

    # Stream the response as a set of lines. This function will return an
    # iterator that yields one line at a time holding only the minimum
    # amount of data chunks in memory to make up a single line
    return response.iter_lines(chunk_size=chunk_size, decode_unicode=True)


def transform_log_lines(
    iter,
    query: Query,
    record_id: str,
    record_event_type: str,
    data_cache: DataCache,
    event_type_fields_mapping: dict,
):
    # iter is a generator iterator that yields a single line at a time
    reader = csv.DictReader(iter)

    # This should cause the reader to request the next line from the iterator
    # which will cause the generator iterator to yield the next line

    row_index = 0

    for row in reader:
        # If we've already seen this log line, skip it
        if data_cache and data_cache.check_and_set_log_line(record_id, row):
            continue

        # Otherwise, pack it up for shipping and yield it for consumption
        yield pack_log_line_into_log(
            query,
            record_id,
            record_event_type,
            row,
            row_index,
            event_type_fields_mapping,
        )

        row_index += 1


def pack_event_record_into_log(
    query: Query,
    record_id: str,
    record: dict,
) -> dict:
    # Make a copy of it so we aren't modifying the row passed by the caller, and
    # set attributes appropriately
    attrs = deepcopy(record)
    if record_id:
        attrs['Id'] = record_id

    message = query.get('event_type', 'SFEvent')
    if 'attributes' in attrs and type(attrs['attributes']) == dict:
        attributes = attrs.pop('attributes')
        if 'type' in attributes and type(attributes['type']) == str:
            attrs['EVENT_TYPE'] = message = \
                query.get('event_type', attributes['type'])

    timestamp_attr = query.get('timestamp_attr', 'CreatedDate')
    if timestamp_attr in attrs:
        created_date = attrs[timestamp_attr]
        message += f' {created_date}'
        timestamp = int(datetime.strptime(
            created_date,
            '%Y-%m-%dT%H:%M:%S.%f%z').timestamp() * 1000,
        )
    else:
        timestamp = int(datetime.now().timestamp() * 1000)

    timestamp_field_name = query.get('rename_timestamp', 'timestamp')
    attrs[timestamp_field_name] = int(timestamp)

    log_entry = {
        'message': message,
        'attributes': attrs,
    }

    if timestamp_field_name == 'timestamp':
        log_entry[timestamp_field_name] = timestamp

    return log_entry


def transform_event_records(iter, query: Query, data_cache: DataCache):
    # iter here is a list which does mean it's entirely held in memory but these
    # are event records not log lines so hopefully it is not as bad.
    # @TODO figure out if we can stream event records
    for record in iter:
        config = query.get_config()

        record_id = record['Id'] if 'Id' in record \
            else generate_record_id(
                config['id'] if 'id' in config else [],
                record,
            )

        # If we've already seen this event record, skip it.
        if data_cache and data_cache.check_and_set_event_id(record_id):
            continue

        # Build a New Relic log record from the SF event record
        yield pack_event_record_into_log(
            query,
            record_id,
            record,
        )


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
        event_type_field_mappings: dict,
        numeric_fields_list: set,
    ):
        self.config = config
        self.data_cache = data_cache
        self.new_relic = new_relic
        self.data_format = data_format
        self.labels = labels
        self.event_type_field_mappings = event_type_field_mappings
        self.numeric_fields_list = numeric_fields_list
        self.max_rows = max(
            self.config.get('max_rows', DEFAULT_MAX_ROWS),
            MAX_ROWS,
        )

    def process_log_record(
        self,
        session: Session,
        query: Query,
        instance_url: str,
        access_token: str,
        record: dict,
    ):
        record_id = str(record['Id'])
        record_event_type = query.get("event_type", record['EventType'])
        record_file_name = record['LogFile']
        interval = record['Interval']

        # NOTE: only Hourly logs can be skipped, because Daily logs can change
        # and the same record_id can contain different data.
        if interval == 'Hourly' and self.data_cache and \
            self.data_cache.can_skip_downloading_logfile(record_id):
            print_info(
                f'Log lines for logfile with id {record_id} already cached, skipping download'
            )
            return None

        if self.data_cache:
            self.data_cache.load_cached_log_lines(record_id)

        load_data(
            transform_log_lines(
                export_log_lines(
                    session,
                    f'{instance_url}{record_file_name}',
                    access_token,
                    self.config.get('chunk_size', DEFAULT_CHUNK_SIZE)
                ),
                query,
                record_id,
                record_event_type,
                self.data_cache,
                self.event_type_field_mappings,
            ),
            self.new_relic,
            self.data_format,
            self.labels,
            self.max_rows,
            self.numeric_fields_list,
        )

    def process_event_records(
        self,
        query: Query,
        records: list[dict],
    ):
        load_data(
            transform_event_records(
                records,
                query,
                self.data_cache,
            ),
            self.new_relic,
            self.data_format,
            self.labels,
            self.max_rows,
            self.numeric_fields_list,
        )

    def execute(
        self,
        session: Session,
        query: Query,
        instance_url: str,
        access_token: str,
        records: list[dict],
    ):
        if is_logfile_response(records):
            for record in records:
                if 'LogFile' in record:
                    self.process_log_record(
                        session,
                        query,
                        instance_url,
                        access_token,
                        record,
                    )

            if self.data_cache:
                self.data_cache.flush()

            return

        self.process_event_records(query, records)

        # Flush the cache
        if self.data_cache:
            self.data_cache.flush()

class PipelineFactory:
    def __init__(self):
        pass

    def new(
        self,
        config: Config,
        data_cache: DataCache,
        new_relic: NewRelic,
        data_format: DataFormat,
        labels: dict,
        event_type_field_mappings: dict,
        numeric_fields_list: set,
    ):
        return Pipeline(
            config,
            data_cache,
            new_relic,
            data_format,
            labels,
            event_type_field_mappings,
            numeric_fields_list,
        )
