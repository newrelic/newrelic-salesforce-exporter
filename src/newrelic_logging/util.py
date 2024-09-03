from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import pytz
from typing import Any, Union


from .telemetry import print_warn


PRIMITIVE_TYPES = (str, int, float, bool, type(None))


def is_logfile_response(record):
    return 'LogFile' in record


def regenerator(items: list[Any], itr):
    yield from items
    yield from itr


def generate_record_id(id_keys: list[str], record: dict) -> str:
    compound_id = ''
    for key in id_keys:
        if key not in record:
            raise Exception(
                f'error building compound id, key \'{key}\' not found'
            )

        compound_id = compound_id + str(record.get(key, ''))

    if compound_id != '':
        m = hashlib.sha3_256()
        m.update(compound_id.encode('utf-8'))
        return m.hexdigest()

    return ''


def maybe_convert_str_to_num(val: str) -> Union[int, str, float]:
    try:
        return int(val)
    except (TypeError, ValueError) as _:
        try:
            return float(val)
        except (TypeError, ValueError) as _:
            print_warn(f'Type conversion error for "{val}"')
            return val


def is_primitive(val: Any) -> bool:
    vt = type(val)

    for t in PRIMITIVE_TYPES:
        if vt == t:
            return True

    return False


def process_query_result_helper(
    item: tuple[str, Any],
    name: list[str] = [],
    vals: list[tuple[str, Any]] = [],
) -> list[tuple[str, Any]]:
    (k, v) = item

    if k == 'attributes':
        return vals

    if is_primitive(v):
        return vals + [('.'.join(name + [k]), v)]

    if not type(v) is dict:
        print_warn(f'ignoring structured element {k} in query result')
        return vals

    new_vals = vals

    for item0 in v.items():
        new_vals = process_query_result_helper(item0, name + [k], new_vals)

    return new_vals


def process_query_result(query_result: dict) -> dict:
    out = {}

    for item in query_result.items():
        for (k, v) in process_query_result_helper(item):
            out[k] = v

    return out


# Make testing easier
def _utcnow():
    return datetime.utcnow()

_UTCNOW = _utcnow

def get_iso_date_with_offset(
    time_lag_minutes: int = 0,
    initial_delay: int = 0,
) -> str:
    return (
        _UTCNOW() - timedelta(
            minutes=(time_lag_minutes + initial_delay)
        )
    ).isoformat(
        timespec='milliseconds'
    ) + 'Z'


# Make testing easier
def _now():
    return datetime.now()

_NOW = _now


def get_timestamp(date_string: str = None):
    if not date_string:
        return int(_NOW().timestamp() * 1000)

    return int(
        datetime.strptime(
            date_string,
            '%Y-%m-%dT%H:%M:%S.%f%z'
        ).timestamp() * 1000
    )


def get_log_line_timestamp(log_line: dict) -> float:
    epoch = log_line.get('TIMESTAMP')

    if epoch:
        return pytz.utc.localize(
            datetime.strptime(epoch, '%Y%m%d%H%M%S.%f')
        ).replace(microsecond=0).timestamp()

    return _UTCNOW().replace(microsecond=0).timestamp()


# NOTE: this sandbox can be jailbroken using the trick to exec statements inside
# an exec block, and run an import (and other tricks):
# https://book.hacktricks.xyz/generic-methodologies-and-resources/python/bypass-python-sandboxes#operators-and-short-tricks
# https://stackoverflow.com/a/3068475/2076108
# Would be better to use a real sandbox like
# https://pypi.org/project/RestrictedPython/ or https://doc.pypy.org/en/latest/sandbox.html
# or parse a small language that only supports funcion calls and binary
# expressions.
#
# @TODO See if we can do this a different way We shouldn't be executing eval ever.

def sandbox(code):
    __import__ = None
    __loader__ = None
    __build_class__ = None
    exec = None


    def sf_time(t: datetime):
        return t.isoformat(timespec='milliseconds') + "Z"

    def now(delta: timedelta = None):
        if delta:
            return sf_time(_UTCNOW() + delta)
        else:
            return sf_time(_UTCNOW())

    try:
        return eval(code)
    except Exception as e:
        return e


def substitute(args: dict, template: str, env: dict) -> str:
    for key, command in env.items():
        args[key] = sandbox(command)
    for key, val in args.items():
        template = template.replace('{' + key + '}', val)
    return template
