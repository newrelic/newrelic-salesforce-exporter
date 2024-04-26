from requests import Session


from ..api import Api
from ..config import Config
from ..telemetry import print_info
from ..util import get_timestamp


def export_limits(
    api: Api,
    session: Session,
    api_ver: str = None,
):
    print_info('Listing limits...')
    return api.list_limits(session, api_ver)


def get_limit_names(config: Config, limits: dict) -> list[str]:
    if 'names' in config:
        return config['names']

    return list(limits)


def build_attributes(limits: dict, key) -> dict:
    attributes = { 'name': key }

    if 'Max' in limits[key]:
        attributes['Max'] = int(limits[key]['Max'])

    if 'Remaining' in limits[key]:
        attributes['Remaining'] = int(limits[key]['Remaining'])

    return attributes


def transform_limits(
    config: Config,
    limits: dict,
):
    limit_names = get_limit_names(config, limits)

    for limit_name in limit_names:
        if not limit_name in limits:
            continue

        yield {
            'message': f'Salesforce Org Limit: {limit_name}',
            'attributes': build_attributes(limits, limit_name),
            'timestamp': get_timestamp(),
        }


class LimitsReceiver:
    def __init__(
        self,
        api: Api,
        options: Config,
    ):
        self.api = api
        self.options = options

    def execute(
        self,
        session: Session,
    ):
        if self.options == None:
            return iter([])

        return transform_limits(
            self.options,
            export_limits(
                self.api,
                session,
                self.options.get('api_ver', None),
            ),
        )


def new_create_receiver_func() -> callable:
    return lambda instance_config, data_cache, api : LimitsReceiver(
        api,
        Config(instance_config['limits']) \
            if 'limits' in instance_config \
            else None,
    )
