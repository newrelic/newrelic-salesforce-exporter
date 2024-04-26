from requests import Session


from . import \
    ConfigException, \
    CacheException, \
    DataFormat, \
    LoginException, \
    NewRelicApiException, \
    SalesforceApiException
from . import config as mod_config, instance
from .query import receiver as query_receiver
from .limits import receiver as limits_receiver
from .newrelic import new_new_relic
from .telemetry import print_info, print_err, new_telemetry, Telemetry
from .http_session import new_retry_session


class Integration:
    def __init__(
        self,
        telemetry: Telemetry,
        instances: list[instance.Instance],
    ):
        self.telemetry = telemetry
        self.instances = instances

    def process_telemetry(self, session: Session):
        if self.telemetry.is_empty():
            print_info("No telemetry data")
            return

        print_info("Sending telemetry data")
        self.telemetry.flush(session)

    def run(self):
        session = new_retry_session()

        try:
            for instance in self.instances:
                print_info(f'Running instance "{instance.name}"')
                instance.harvest(session)
                self.process_telemetry(session)
        except LoginException as e:
            print_err(f'authentication failed: {e}')
            raise e
        except SalesforceApiException as e:
            print_err(f'exception while fetching data from Salesforce: {e}')
            raise e
        except CacheException as e:
            print_err(f'exception while accessing backend cache: {e}')
            raise e
        except NewRelicApiException as e:
            print_err(f'exception while posting data to New Relic: {e}')
            raise e
        except Exception as e:
            print_err(f'unknown exception occurred: {e}')
            raise e
