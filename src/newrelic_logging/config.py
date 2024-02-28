import os
import re
from types import SimpleNamespace
from typing import Any


BOOL_TRUE_VALS = ['true', '1', 'on', 'yes']
NOT_FOUND = SimpleNamespace()


def _get_nested_helper(val: Any, arr: list[str] = [], index: int = 0) -> Any:
    if index == len(arr):
        return NOT_FOUND
    elif type(val) is dict:
        key = arr[index]
        if index == len(arr) - 1:
            return val[key] if key in val else NOT_FOUND
        return _get_nested_helper(val[key], arr, index + 1) \
            if key in val else NOT_FOUND
    elif type(val) is list:
        key = arr[index]
        if key.isdigit():
            arr_index = int(key)
            if arr_index < 0 or arr_index >= len(val):
                return NOT_FOUND
            if index == len(arr) - 1:
                return val[arr_index]
            return _get_nested_helper(val[arr_index], arr, index + 1)

    return NOT_FOUND


def get_nested(d: dict, path: str) -> Any:
    return _get_nested_helper(d, path.split('.'))


def getenv(var_name, default = None, prefix = ''):
    return os.environ.get(prefix + var_name, default)


def tobool(s):
    if s == None:
        return False
    elif type(s) == bool:
        return s
    elif type(s) == str:
        if s.lower() in BOOL_TRUE_VALS:
            return True
        return False

    return bool(s)


class Config:
    def __init__(self, config: dict, prefix: str = ''):
        self.config = config
        self.prefix = prefix

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value

    def __len__(self):
        return len(self.config)

    def __contains__(self, key):
        return key in self.config

    def set_prefix(self, prefix: str) -> None:
        self.prefix = prefix

    def getenv(self, env_var_name: str, default = None) -> str:
        return getenv(env_var_name, default, self.prefix)

    def get(self, key: str, default = None, allow_none = False) -> Any:
        val = get_nested(self.config, key)
        if not val == NOT_FOUND and not allow_none and not val == None:
            return val

        return self.getenv(
            re.sub(r'[^a-zA-Z0-9_]', '_', key.upper()),
            default,
        )

    def get_int(self, key: str, default = None) -> int:
        val = self.get(key, default)
        return int(val) if val else val

    def get_bool(self, key: str, default = None) -> bool:
        return tobool(self.get(key, default))

    def sub(self, key: str, default: dict = {}, prefix: str = None):
        val = get_nested(self.config, key)
        if val == None or val == NOT_FOUND:
            return Config(default, self.prefix if prefix == None else prefix )

        if not type(val) is dict:
            raise Exception(f'can not create sub config for property {key} of type {type(val)} because it is not a dictionary')

        return Config(val, self.prefix if prefix == None else prefix)
