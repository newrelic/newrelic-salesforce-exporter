from . import CacheException, ConfigException, DataFormat, NewRelicApiException
from .api import Api
from .auth import \
    Authenticator, \
    make_auth_from_config, \
    make_auth_from_env, \
    SF_TOKEN_URL
from . import cache, newrelic
from .config import Config
from .instance import Instance
from .integration import Integration
from .pipeline import Pipeline
from .telemetry import print_info, Telemetry


class Factory:
    def __init__(self):
        pass

    def new_backend_factory(self):
        return cache.BackendFactory()

    def new_data_cache(
        self,
        instance_config: Config,
        backend_factory: cache.BackendFactory,
    ) -> cache.DataCache:
        if not instance_config.get_bool(
            cache.CONFIG_CACHE_ENABLED,
            cache.DEFAULT_CACHE_ENABLED,
        ):
            print_info('Cache disabled')
            return None

        print_info('Cache enabled')

        try:
            return cache.DataCache(
                backend_factory.new_backend(instance_config),
                instance_config.get_int(
                    cache.CONFIG_REDIS_EXPIRE_DAYS,
                    cache.DEFAULT_REDIS_EXPIRE_DAYS,
                )
            )
        except Exception as e:
            raise CacheException(f'failed creating backend: {e}')

    def new_authenticator(
        self,
        instance_config: Config,
        data_cache: cache.DataCache,
    ) -> Authenticator:
        token_url = instance_config.get('token_url', env_var_name=SF_TOKEN_URL)

        if not token_url:
            raise ConfigException('token_url', 'missing token URL')

        if 'auth' in instance_config:
            return Authenticator(
                token_url,
                make_auth_from_config(instance_config.sub('auth')),
                data_cache,
            )

        return Authenticator(
            token_url,
            make_auth_from_env(instance_config),
            data_cache
        )

    def new_api(self, authenticator: Authenticator, api_ver: str):
        return Api(authenticator, api_ver)

    def new_pipeline(
        self,
        config: Config,
        data_cache: cache.DataCache,
        new_relic: newrelic.NewRelic,
        data_format: DataFormat,
        labels: dict,
        numeric_fields_list: set,
    ) -> Pipeline:
        return Pipeline(
            config,
            data_cache,
            new_relic,
            data_format,
            labels,
            numeric_fields_list,
        )

    def new_instance(
        self,
        factory,
        instance_name: str,
        instance_config: Config,
        data_format: DataFormat,
        new_relic: newrelic.NewRelic,
        receivers: list[callable],
        labels: dict,
        numeric_fields_list: set = set(),
    ) -> Instance:
        data_cache = factory.new_data_cache(
            instance_config,
            factory.new_backend_factory(),
        )

        api = factory.new_api(
            factory.new_authenticator(instance_config, data_cache),
            instance_config.get('api_ver', '55.0'),
        )

        p = factory.new_pipeline(
            instance_config,
            data_cache,
            new_relic,
            data_format,
            labels,
            numeric_fields_list,
        )

        for r in receivers:
            p.add_receiver(r(
                instance_config,
                data_cache,
                api
            ))

        return Instance(
            instance_name,
            api,
            p,
        )

    def new_integration(
        self,
        factory,
        config: Config,
        receivers: list[callable],
        numeric_fields_list: set = set(),
        instance_index: int = None
    ):
        if not 'instances' in config or len(config['instances']) == 0:
            raise ConfigException('no instances found to run')

        data_format = config.get('newrelic.data_format', 'logs').lower()
        if data_format == 'logs':
            data_format = DataFormat.LOGS
        elif data_format == 'events':
            data_format = DataFormat.EVENTS
        else:
            raise ConfigException(f'invalid data format {data_format}')

        new_relic = factory.new_new_relic(config, data_format)
        telemetry = factory.new_telemetry(config, new_relic)
        instances = []

        def append_instance(inst, index):
            if not 'name' in inst:
                raise ConfigException(f'missing instance name for instance {inst}')

            instance_config = config.sub(f'instances.{index}.arguments')
            instance_config.set_prefix(
                instance_config['auth_env_prefix'] \
                if 'auth_env_prefix' in instance_config else ''
            )

            labels = inst['labels'] if 'labels' in inst else {}
            labels['nr-labs'] = 'data'

            instances.append(factory.new_instance(
                factory,
                inst['name'],
                instance_config,
                data_format,
                new_relic,
                receivers,
                labels,
                numeric_fields_list,
            ))
        
        # Either create an integration with all instance or a single instance.
        if instance_index is None:
            for index, inst in enumerate(config['instances']):
                append_instance(inst, index)
        else:
            inst = config['instances'][instance_index]
            append_instance(inst, instance_index)

        return Integration(telemetry, instances)

    def new_new_relic(self, config: Config, data_format: DataFormat):
        license_key = config.get(
            'newrelic.license_key',
            env_var_name=newrelic.NR_LICENSE_KEY,
        )
        if not license_key:
            raise NewRelicApiException(f'missing New Relic license key')

        region = config.get('newrelic.api_endpoint')
        if not region:
            raise NewRelicApiException(f'missing New Relic API region')

        region_l = region.lower()
        if not region_l == 'us' and not region_l == 'eu':
            raise NewRelicApiException(f'invalid New Relic API region {region}')

        if data_format == DataFormat.EVENTS:
            account_id = config.get(
                'newrelic.account_id',
                env_var_name=newrelic.NR_ACCOUNT_ID,
            )
            if not account_id:
                raise NewRelicApiException(f'missing New Relic account ID')

            return newrelic.NewRelic(
                license_key,
                None,
                (
                    newrelic.US_EVENTS_ENDPOINT if region_l == 'us' \
                        else newrelic.EU_EVENTS_ENDPOINT
                ).format(account_id=account_id)
            )

        return newrelic.NewRelic(
            license_key,
            newrelic.US_LOGGING_ENDPOINT if region_l == 'us' \
                else newrelic.EU_LOGGING_ENDPOINT,
            None
        )

    def new_telemetry(
        self,
        config: Config,
        new_relic: newrelic.NewRelic,
    ):
        return Telemetry(
            config['integration_name'] \
                if 'integration_name' in config \
                else 'com.newrelic.labs.salesforce.exporter',
            new_relic
        )
