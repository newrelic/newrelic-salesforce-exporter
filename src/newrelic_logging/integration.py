from requests import Session

from . import \
    ConfigException, \
    CacheException, \
    DataFormat, \
    LoginException, \
    NewRelicApiException, \
    SalesforceApiException
from . import auth
from . import cache
from . import config as mod_config
from . import newrelic
from . import pipeline
from .http_session import new_retry_session
from .salesforce import SalesForce
from .telemetry import Telemetry, print_info, print_err


# @TODO: move queries to the instance level, so we can have different queries for
# each instance.
# @TODO: also keep general queries that apply to all instances.


class Integration:
    def __init__(
        self,
        config: mod_config.Config,
        event_type_fields_mapping: dict = {},
        numeric_fields_list: set = set(),
        initial_delay: int = 0,
    ):
        Telemetry(config["integration_name"])

        data_format = config.get('newrelic.data_format', 'logs').lower()
        if data_format == 'logs':
            data_format = DataFormat.LOGS
        elif data_format == 'events':
            data_format = DataFormat.EVENTS
        else:
            raise ConfigException(f'invalid data format {data_format}')

        # Fill credentials for NR APIs

        new_relic = newrelic.New(config)

        self.instances = []
        for count, instance in enumerate(config['instances']):
            instance_name = instance['name']
            labels = instance['labels']
            labels['nr-labs'] = 'data'
            instance_config = config.sub(f'instances.{count}.arguments')
            instance_config.set_prefix(
                instance_config['auth_env_prefix'] \
                if 'auth_env_prefix' in instance_config else ''
            )

            data_cache = cache.New(instance_config)
            authenticator = auth.New(instance_config, data_cache)

            self.instances.append({
                'client': SalesForce(
                    instance_name,
                    instance_config,
                    data_cache,
                    authenticator,
                    pipeline.New(
                        instance_config,
                        data_cache,
                        new_relic,
                        data_format,
                        labels,
                        event_type_fields_mapping,
                        numeric_fields_list,
                    ),
                    initial_delay,
                    config['queries'] if 'queries' in config else None,
                ),
                'name': instance_name,
            })

    def process_telemetry(self):
        if not Telemetry().is_empty():
            print_info("Sending telemetry data")
            self.process_logs(Telemetry().build_model(), {}, None)
            Telemetry().clear()
        else:
            print_info("No telemetry data")

    def auth_and_fetch(
        self,
        client: SalesForce,
        session: Session,
        retry: bool = True,
    ) -> None:

        try:
            client.authenticate(session)
            return client.fetch_logs(session)
        except LoginException as e:
            print_err(f'authentication failed: {e}')
        except SalesforceApiException as e:
            if e.err_code == 401:
                if retry:
                    print_err('authentication failed, retrying...')
                    client.clear_auth()
                    self.auth_and_fetch(
                        client,
                        session,
                        False,
                    )
                    return

                print_err(f'exception while fetching data from SF: {e}')
                return

            print_err(f'exception while fetching data from SF: {e}')
        except CacheException as e:
            print_err(f'exception while accessing Redis cache: {e}')
        except NewRelicApiException as e:
            print_err(f'exception while posting data to New Relic: {e}')
        except Exception as e:
            print_err(f'unknown exception occurred: {e}')

    def run(self):
        for instance in self.instances:
            print_info(f"Running instance '{instance['name']}'")
            self.auth_and_fetch(instance['client'], new_retry_session())
            self.process_telemetry()
