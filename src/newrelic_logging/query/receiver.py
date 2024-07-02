from copy import deepcopy
import csv
from requests import Session


from . import Query, QueryFactory
from ..api import Api
from ..cache import DataCache
from .. import config as mod_config
from ..telemetry import print_info, print_warn
from ..util import \
    generate_record_id, \
    get_timestamp, \
    get_iso_date_with_offset, \
    get_log_line_timestamp, \
    is_logfile_response, \
    process_query_result, \
    regenerator


DEFAULT_CHUNK_SIZE = 4096
SALESFORCE_CREATED_DATE_QUERY = \
    "SELECT Id,EventType,CreatedDate,LogDate,Interval,LogFile,Sequence From EventLogFile Where CreatedDate>={" \
    "from_timestamp} AND CreatedDate<{to_timestamp} AND Interval='{log_interval_type}'"
SALESFORCE_LOG_DATE_QUERY = \
    "SELECT Id,EventType,CreatedDate,LogDate,Interval,LogFile,Sequence From EventLogFile Where LogDate>={" \
    "from_timestamp} AND LogDate<{to_timestamp} AND Interval='{log_interval_type}'"


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
    api: Api,
    session: Session,
    log_file_path: str,
    chunk_size: int,
):
    print_info(f'Downloading log lines for log file: {log_file_path}')
    return api.get_log_file(session, log_file_path, chunk_size)


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
        if data_cache and data_cache.check_or_set_log_line(record_id, row):
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


def pack_query_record_into_log(
    query: Query,
    record_id: str,
    record: dict,
) -> dict:
    attrs = process_query_result(record)
    if record_id:
        attrs['Id'] = record_id

    message = query.get('event_type', 'SFEvent')
    if 'attributes' in record and type(record['attributes']) == dict:
        attributes = record['attributes']
        if 'type' in attributes and type(attributes['type']) == str:
            attrs['EVENT_TYPE'] = message = \
                query.get('event_type', attributes['type'])

    timestamp_attr = query.get('timestamp_attr', 'CreatedDate')
    if timestamp_attr in attrs:
        created_date = attrs[timestamp_attr]
        message += f' {created_date}'
        timestamp = get_timestamp(created_date)
    else:
        timestamp = get_timestamp()

    timestamp_field_name = query.get('rename_timestamp', 'timestamp')
    attrs[timestamp_field_name] = timestamp

    log_entry = {
        'message': message,
        'attributes': attrs,
    }

    if timestamp_field_name == 'timestamp':
        log_entry[timestamp_field_name] = timestamp

    return log_entry


def transform_query_records(iter, query: Query, data_cache: DataCache):
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
        if data_cache and data_cache.check_or_set_record_id(record_id):
            continue

        # Build a New Relic log record from the SF event record
        yield pack_query_record_into_log(
            query,
            record_id,
            record,
        )


def is_logs_enabled(instance_config: mod_config.Config) -> bool:
    if not 'logs_enabled' in instance_config:
        return True

    return mod_config.tobool(instance_config['logs_enabled'])


def get_instance_queries(instance_config: mod_config.Config) -> list[dict]:
    if not 'queries' in instance_config or \
        not type(instance_config['queries']) is list:
        return None

    return instance_config['queries']


def get_default_query(date_field: str) -> str:
    if date_field.lower() == 'logdate':
        return SALESFORCE_LOG_DATE_QUERY

    return SALESFORCE_CREATED_DATE_QUERY


def build_queries(
    instance_config: mod_config.Config,
    global_queries: list[dict],
    date_field: str,
) -> list[dict]:
    queries = []

    instance_queries = get_instance_queries(instance_config)
    if instance_queries:
        queries.extend(instance_queries)

    if global_queries:
        queries.extend(global_queries)

    if len(queries) == 0 and is_logs_enabled(instance_config):
        queries.append({ 'query': get_default_query(date_field) })

    return queries


class QueryReceiver:
    def __init__(
        self,
        data_cache: DataCache,
        api: Api,
        query_factory: QueryFactory,
        queries: list[dict],
        event_type_fields_mapping: dict,
        initial_delay: int,
        time_lag_minutes: int,
        generation_interval: str,
        read_chunk_size: int,
    ):
        self.data_cache = data_cache
        self.api = api
        self.query_factory = query_factory
        self.event_type_fields_mapping = event_type_fields_mapping
        self.time_lag_minutes = time_lag_minutes
        self.generation_interval = generation_interval
        self.last_to_timestamp = get_iso_date_with_offset(
            self.time_lag_minutes,
            initial_delay,
        )
        self.queries = queries
        self.read_chunk_size = read_chunk_size

    def process_log_record(
        self,
        session: Session,
        query: Query,
        record: dict,
    ):
        record_id = str(record['Id'])
        record_event_type = query.get('event_type', record['EventType'])
        log_file_path = record['LogFile']
        interval = record['Interval']

        # NOTE: only Hourly logs can be skipped, because Daily logs can change
        # and the same record_id can contain different data.
        if interval == 'Hourly' and self.data_cache and \
            self.data_cache.can_skip_downloading_logfile(record_id):
            print_info(
                f'Log lines for logfile with id {record_id} already cached, skipping download'
            )
            return iter([])

        return transform_log_lines(
            export_log_lines(
                self.api,
                session,
                log_file_path,
                self.read_chunk_size,
            ),
            query,
            record_id,
            record_event_type,
            self.data_cache,
            self.event_type_fields_mapping,
        )

    def process_query_records(
        self,
        query: Query,
        iter,
    ):
        return transform_query_records(
            iter,
            query,
            self.data_cache,
        )

    def process_records(
        self,
        session: Session,
        query: Query,
        iter,
    ):
        first = next(iter, None)
        if first is None:
            return

        reiter = regenerator([first], iter)

        if is_logfile_response(first):
            for record in reiter:
                if 'LogFile' in record:
                    yield from self.process_log_record(
                        session,
                        query,
                        record,
                    )

                if self.data_cache:
                    self.data_cache.flush()

            return

        yield from self.process_query_records(query, reiter)

        # Flush the cache
        if self.data_cache:
            self.data_cache.flush()

    def slide_time_range(self):
        self.last_to_timestamp = get_iso_date_with_offset(
            self.time_lag_minutes
        )

    def execute(
        self,
        session: Session,
    ):
        if len(self.queries) == 0:
            return

        for q in self.queries:
            query = self.query_factory.new(
                self.api,
                q,
                self.time_lag_minutes,
                self.last_to_timestamp,
                self.generation_interval,
            )

            yield from self.process_records(
                session,
                query,
                query.execute(session),
            )

        self.slide_time_range()


def new_create_receiver_func(
    config: mod_config.Config,
    query_factory: QueryFactory,
    event_type_fields_mapping: dict,
    initial_delay: int,
) -> callable:
    return lambda instance_config, data_cache, api : QueryReceiver(
        data_cache,
        api,
        query_factory,
        build_queries(
            instance_config,
            config['queries'] if 'queries' in config else None,
            instance_config.get(
                mod_config.CONFIG_DATE_FIELD,
                mod_config.DATE_FIELD_LOG_DATE if not data_cache \
                    else mod_config.DATE_FIELD_CREATE_DATE,
            )
        ),
        event_type_fields_mapping,
        initial_delay,
        instance_config.get(
            mod_config.CONFIG_TIME_LAG_MINUTES,
            mod_config.DEFAULT_TIME_LAG_MINUTES if not data_cache else 0,
        ),
        instance_config.get(
            mod_config.CONFIG_GENERATION_INTERVAL,
            mod_config.DEFAULT_GENERATION_INTERVAL,
        ),
        instance_config.get('chunk_size', DEFAULT_CHUNK_SIZE)
    )
