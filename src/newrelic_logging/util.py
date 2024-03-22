from datetime import datetime, timedelta
import hashlib
from typing import Union

from .telemetry import print_warn


def is_logfile_response(records):
    if len(records) > 0:
        return 'LogFile' in records[0]

    return True


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
