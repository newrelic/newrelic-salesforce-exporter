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
from . import query
from . import pipeline
from . import salesforce
from .http_session import new_retry_session
from .telemetry import print_err, print_info, print_warn, Telemetry


# @TODO: move queries to the instance level, so we can have different queries for
# each instance.
# @TODO: also keep general queries that apply to all instances.

def build_instance(
    config: mod_config.Config,
    auth_factory: auth.AuthenticatorFactory,
    cache_factory: cache.CacheFactory,
    pipeline_factory: pipeline.PipelineFactory,
    salesforce_factory: salesforce.SalesForceFactory,
    query_factory: query.QueryFactory,
    new_relic: newrelic.NewRelic,
    data_format: DataFormat,
    event_type_fields_mapping: dict,
    numeric_fields_list: set,
    initial_delay: int,
    instance: dict,
    index: int,
):
    instance_name = instance['name']
    labels = instance['labels']
    labels['nr-labs'] = 'data'
    instance_config = config.sub(f'instances.{index}.arguments')
    instance_config.set_prefix(
        instance_config['auth_env_prefix'] \
        if 'auth_env_prefix' in instance_config else ''
    )

    data_cache = cache_factory.new(instance_config)
    authenticator = auth_factory.new(instance_config, data_cache)

    return {
        'client': salesforce_factory.new(
            instance_name,
            instance_config,
            data_cache,
            authenticator,
            pipeline_factory.new(
                instance_config,
                data_cache,
                new_relic,
                data_format,
                labels,
                event_type_fields_mapping,
                numeric_fields_list,
            ),
            query_factory,
            initial_delay,
            config['queries'] if 'queries' in config else None,
        ),
        'name': instance_name,
    }

class Integration:
    def __init__(
        self,
        config: mod_config.Config,
        auth_factory: auth.AuthenticatorFactory,
        cache_factory: cache.CacheFactory,
        pipeline_factory: pipeline.PipelineFactory,
        salesforce_factory: salesforce.SalesForceFactory,
        query_factory: query.QueryFactory,
        newrelic_factory: newrelic.NewRelicFactory,
        event_type_fields_mapping: dict = {},
        numeric_fields_list: set = set(),
        initial_delay: int = 0,
    ):
        Telemetry(
            config['integration_name'] if 'integration_name' in config \
                else 'com.newrelic.labs.sfdc.eventlogfiles'
        )

        data_format = config.get('newrelic.data_format', 'logs').lower()
        if data_format == 'logs':
            data_format = DataFormat.LOGS
        elif data_format == 'events':
            data_format = DataFormat.EVENTS
        else:
            raise ConfigException(f'invalid data format {data_format}')

        self.new_relic = newrelic_factory.new(config)
        self.instances = []

        if not 'instances' in config or len(config['instances']) == 0:
            print_warn('no instances found to run')
            return

        for index, instance in enumerate(config['instances']):
            self.instances.append(build_instance(
                config,
                auth_factory,
                cache_factory,
                pipeline_factory,
                salesforce_factory,
                query_factory,
                self.new_relic,
                data_format,
                event_type_fields_mapping,
                numeric_fields_list,
                initial_delay,
                instance,
                index,
            ))

    def process_telemetry(self, session: Session):
        if Telemetry().is_empty():
            print_info("No telemetry data")
            return

        print_info("Sending telemetry data")
        self.new_relic.post_logs(session, Telemetry().build_model())
        Telemetry().clear()

    def auth_and_fetch(
        self,
        client: salesforce.SalesForce,
        session: Session,
    ) -> None:
        try:
            client.authenticate(session)
            client.fetch_logs(session)
        except LoginException as e:
            print_err(f'authentication failed: {e}')
        except SalesforceApiException as e:
            print_err(f'exception while fetching data from SF: {e}')
        except CacheException as e:
            print_err(f'exception while accessing Redis cache: {e}')
        except NewRelicApiException as e:
            print_err(f'exception while posting data to New Relic: {e}')
        except Exception as e:
            print_err(f'unknown exception occurred: {e}')

    def run(self):
        session = new_retry_session()

        for instance in self.instances:
            print_info(f'Running instance "{instance["name"]}"')
            self.auth_and_fetch(instance['client'], session)
            self.process_telemetry(session)
