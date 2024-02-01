# Integration Telemetry

import time
import json

def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance

@singleton
class Telemetry:
    logs = []
    integration_name = None

    def __init__(self, integration_name: str) -> None:
        self.integration_name = integration_name
    
    def is_empty(self):
        return len(self.logs) == 0
    
    def log_info(self, msg: str):
        self.record_log(msg, "info")
    
    def log_err(self, msg: str):
        self.record_log(msg, "error")
    
    def log_warn(self, msg: str):
        self.record_log(msg, "warn")
    
    def record_log(self, msg: str, level: str):
        log = {
            "timestamp": round(time.time() * 1000),
            "message": msg,
            "attributes": {
                "service": self.integration_name,
                "level": level
            }
        }
        self.logs.append(log)
    
    def clear(self):
        self.logs = []

    def build_model(self):
        return [{
            "log_entries": self.logs
        }]
    
def print_log(msg: str, level: str):
    print(json.dumps({
        "message": msg,
        "level": level
    }))

def print_info(msg: str):
    print_log(msg, "info")

def print_err(msg: str):
    print_log(msg, "error")

def print_warn(msg: str):
    print_log(msg, "warn")
