from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta
import jwt
from requests import RequestException, Session

from . import ConfigException, LoginException
from .cache import DataCache
from .config import Config
from .telemetry import print_err, print_info, print_warn


AUTH_CACHE_KEY = 'com.newrelic.labs.sf_auth'
SF_GRANT_TYPE = 'SF_GRANT_TYPE'
SF_CLIENT_ID =  'SF_CLIENT_ID'
SF_CLIENT_SECRET = 'SF_CLIENT_SECRET'
SF_USERNAME = 'SF_USERNAME'
SF_PASSWORD = 'SF_PASSWORD'
SF_PRIVATE_KEY = 'SF_PRIVATE_KEY'
SF_SUBJECT = 'SF_SUBJECT'
SF_AUDIENCE = 'SF_AUDIENCE'
SF_TOKEN_URL = 'SF_TOKEN_URL'


class Authenticator:
    def __init__(
        self,
        token_url: str,
        auth_data: dict,
        data_cache: DataCache
    ):
        self.token_url = token_url
        self.auth_data = auth_data
        self.data_cache = data_cache
        self.access_token = None
        self.instance_url = None

    def get_access_token(self) -> str:
        return self.access_token

    def get_instance_url(self) -> str:
        return self.instance_url

    def get_grant_type(self) -> str:
        return self.auth_data['grant_type']

    def set_auth_data(self, access_token: str, instance_url: str) -> None:
        self.access_token = access_token
        self.instance_url = instance_url

    def clear_auth(self) -> None:
        self.set_auth_data(None, None)

        if self.data_cache:
            try:
                # @TODO need to change all the places where redis is explicitly
                # referenced since this breaks encapsulation.
                self.data_cache.backend.redis.delete(AUTH_CACHE_KEY)
            except Exception as e:
                print_warn(f'Failed deleting data from cache: {e}')

    def load_auth_from_cache(self) -> bool:
        try:
            auth_exists = self.data_cache.backend.redis.exists(AUTH_CACHE_KEY)
            if auth_exists:
                print_info('Retrieving credentials from Redis.')
                try:
                    auth = self.data_cache.backend.redis.hmget(
                        AUTH_CACHE_KEY,
                        ['access_token', 'instance_url'],
                    )

                    self.set_auth_data(
                        auth[0],
                        auth[1],
                    )

                    return True
                except Exception as e:
                    print_err(f"Failed getting 'auth' key: {e}")
        except Exception as e:
            print_err(f"Failed checking 'auth' key: {e}")

        return False

    def store_auth(self, auth_resp: dict) -> None:
        self.access_token = auth_resp['access_token']
        self.instance_url = auth_resp['instance_url']

        if self.data_cache:
            print_info('Storing credentials in cache.')

            auth = {
                'access_token': self.access_token,
                'instance_url': self.instance_url,
            }

            try:
                self.data_cache.backend.redis.hmset(AUTH_CACHE_KEY, auth)
            except Exception as e:
                print_warn(f"Failed storing data in cache: {e}")

    def authenticate_with_jwt(self, session: Session) -> None:
        private_key_file = self.auth_data['private_key']
        client_id = self.auth_data['client_id']
        subject = self.auth_data['subject']
        audience = self.auth_data['audience']
        exp = int((datetime.utcnow() - timedelta(minutes=5)).timestamp())

        with open(private_key_file, 'r') as f:
            try:
                private_key = f.read()
                key = serialization.load_ssh_private_key(private_key.encode(), password=b'')
            except ValueError as e:
                raise LoginException(f'authentication failed for {self.instance_name}. error message: {str(e)}')

        jwt_claim_set = {
            "iss": client_id,
            "sub": subject,
            "aud": audience,
            "exp": exp
        }

        signed_token = jwt.encode(
            jwt_claim_set,
            key,
            algorithm='RS256',
        )

        params = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signed_token,
            "format": "json"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        try:
            print_info(f'retrieving salesforce token at {self.token_url}')
            resp = session.post(self.token_url, params=params,
                                headers=headers)
            if resp.status_code != 200:
                raise LoginException(f'sfdc token request failed. http-status-code:{resp.status_code}, reason: {resp.text}')

            self.store_auth(resp.json())
        except ConnectionError as e:
            raise LoginException(f'authentication failed for sfdc instance {self.instance_name}') from e
        except RequestException as e:
            raise LoginException(f'authentication failed for sfdc instance {self.instance_name}') from e

    def authenticate_with_password(self, session: Session) -> None:
        client_id = self.auth_data['client_id']
        client_secret = self.auth_data['client_secret']
        username = self.auth_data['username']
        password = self.auth_data['password']

        params = {
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        try:
            print_info(f'retrieving salesforce token at {self.token_url}')
            resp = session.post(self.token_url, params=params,
                                headers=headers)
            if resp.status_code != 200:
                raise LoginException(f'salesforce token request failed. status-code:{resp.status_code}, reason: {resp.reason}')

            self.store_auth(resp.json())
        except ConnectionError as e:
            raise LoginException(f'authentication failed for sfdc instance {self.instance_name}') from e
        except RequestException as e:
            raise LoginException(f'authentication failed for sfdc instance {self.instance_name}') from e

    def authenticate(self, session: Session) -> None:
        if self.data_cache and self.load_auth_from_cache():
            return

        oauth_type = self.get_grant_type()
        if oauth_type == 'password':
            self.authenticate_with_password(session)
            print_info('Correctly authenticated with user/pass flow')
            return

        self.authenticate_with_jwt(session)
        print_info('Correctly authenticated with JWT flow')

    def reauthenticate(self, session: Session) -> None:
        self.clear_auth()
        self.authenticate(session)

def validate_oauth_config(auth: dict) -> dict:
    if not auth['client_id']:
        raise ConfigException('client_id', 'missing OAuth client id')

    if not auth['client_secret']:
        raise ConfigException(
            'client_secret',
            'missing OAuth client secret',
        )

    if not auth['username']:
        raise ConfigException('username', 'missing OAuth username')

    if not auth['password']:
        raise ConfigException('password', 'missing OAuth client secret')

    return auth


def validate_jwt_config(auth: dict) -> dict:
    if not auth['client_id']:
        raise ConfigException('client_id', 'missing JWT client id')

    if not auth['private_key']:
        raise ConfigException('private_key', 'missing JWT private key')

    if not auth['subject']:
        raise ConfigException('subject', 'missing JWT subject')

    if not auth['audience']:
        raise ConfigException('audience', 'missing JWT audience')

    return auth


def make_auth_from_config(auth: Config) -> dict:
    grant_type = auth.get(
        'grant_type',
        'password',
        env_var_name=SF_GRANT_TYPE,
    ).lower()

    if grant_type == 'password':
        return validate_oauth_config({
            'grant_type': grant_type,
            'client_id': auth.get('client_id', env_var_name=SF_CLIENT_ID),
            'client_secret': auth.get(
                'client_secret',
                env_var_name=SF_CLIENT_SECRET
            ),
            'username': auth.get('username', env_var_name=SF_USERNAME),
            'password': auth.get('password', env_var_name=SF_PASSWORD),
        })

    if grant_type == 'urn:ietf:params:oauth:grant-type:jwt-bearer':
        return validate_jwt_config({
            'grant_type': grant_type,
            'client_id': auth.get('client_id', env_var_name=SF_CLIENT_ID),
            'private_key': auth.get('private_key', env_var_name=SF_PRIVATE_KEY),
            'subject': auth.get('subject', env_var_name=SF_SUBJECT),
            'audience': auth.get('audience', env_var_name=SF_AUDIENCE),
        })

    raise Exception(f'Wrong or missing grant_type')


def make_auth_from_env(config: Config) -> dict:
    grant_type = config.getenv(SF_GRANT_TYPE, 'password').lower()

    if grant_type == 'password':
        return validate_oauth_config({
            'grant_type': grant_type,
            'client_id': config.getenv(SF_CLIENT_ID),
            'client_secret': config.getenv(SF_CLIENT_SECRET),
            'username': config.getenv(SF_USERNAME),
            'password': config.getenv(SF_PASSWORD),
        })

    if grant_type == 'urn:ietf:params:oauth:grant-type:jwt-bearer':
        return validate_jwt_config({
            'grant_type': grant_type,
            'client_id': config.getenv(SF_CLIENT_ID),
            'private_key': config.getenv(SF_PRIVATE_KEY),
            'subject': config.getenv(SF_SUBJECT),
            'audience': config.getenv(SF_AUDIENCE),
        })

    raise Exception(f'Wrong or missing grant_type')


class AuthenticatorFactory:
    def __init__(self):
        pass

    def new(self, config: Config, data_cache: DataCache) -> Authenticator:
        token_url = config.get('token_url', env_var_name=SF_TOKEN_URL)

        if not token_url:
            raise ConfigException('token_url', 'missing token URL')

        if 'auth' in config:
            return Authenticator(
                token_url,
                make_auth_from_config(config.sub('auth')),
                data_cache,
            )

        return Authenticator(
            token_url,
            make_auth_from_env(config),
            data_cache
        )
