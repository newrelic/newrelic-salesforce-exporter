from .query import Query
import string

# NOTE: this sandbox can be jailbroken using the trick to exec statements inside an exec block, and run an import (and other tricks):
# https://book.hacktricks.xyz/generic-methodologies-and-resources/python/bypass-python-sandboxes#operators-and-short-tricks
# https://stackoverflow.com/a/3068475/2076108
# Would be better to use a real sandbox like https://pypi.org/project/RestrictedPython/ or https://doc.pypy.org/en/latest/sandbox.html
# or parse a small language that only supports funcion calls and binary expressions.
def sandbox(code):
    __import__ = None
    __loader__ = None
    __build_class__ = None
    exec = None
    
    from datetime import datetime, timedelta

    def sf_time(t: datetime):
        return t.isoformat(timespec='milliseconds') + "Z"
    
    def now(delta: timedelta = None):
        if delta:
            return sf_time(datetime.utcnow() + delta)
        else:
            return sf_time(datetime.utcnow())
    
    try:
        return eval(code)
    except Exception as e:
        return e

def substitute(args: dict, query_template: str, env: dict) -> str:
    for key, command in env.items():
        args[key] = sandbox(command)
    for key, val in args.items():
        query_template = query_template.replace('{' + key + '}', val)
    return query_template
