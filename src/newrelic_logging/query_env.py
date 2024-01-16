from .query import Query
import string

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
