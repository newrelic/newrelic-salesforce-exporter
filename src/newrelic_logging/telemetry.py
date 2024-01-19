# Integration Telemetry

import time

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