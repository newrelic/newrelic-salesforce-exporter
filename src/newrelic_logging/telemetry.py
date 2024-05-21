import json
import time
from requests import Session


from .config import Config
from .newrelic import NewRelic


class Telemetry:
    logs = []
    integration_name = None

    def __init__(self, integration_name: str, new_relic: NewRelic) -> None:
        self.integration_name = integration_name
        self.new_relic = new_relic

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

    def flush(self, session: Session):
        self.new_relic.post_logs(
            session,
            [{
                "common": {},
                "logs": self.logs,
            }]
        )
        self.clear()


def print_log(msg: str, level: str):
    print(json.dumps({
        "message": msg,
        "timestamp": round(time.time() * 1000),
        "level": level
    }))


def print_info(msg: str):
    print_log(msg, "info")


def print_err(msg: str):
    print_log(msg, "error")


def print_warn(msg: str):
    print_log(msg, "warn")


def new_telemetry(
   config: Config,
   new_relic: NewRelic,
):
    return Telemetry(
        config['integration_name'] \
            if 'integration_name' in config \
            else 'com.newrelic.labs.salesforce.exporter',
        new_relic
    )
