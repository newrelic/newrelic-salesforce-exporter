SF_GRANT_TYPE = 'SF_GRANT_TYPE'
SF_CLIENT_ID =  'SF_CLIENT_ID'
SF_CLIENT_SECRET = 'SF_CLIENT_SECRET'
SF_USERNAME = 'SF_USERNAME'
SF_PASSWORD = 'SF_PASSWORD'
SF_PRIVATE_KEY = 'SF_PRIVATE_KEY'
SF_SUBJECT = 'SF_SUBJECT'
SF_AUDIENCE = 'SF_AUDIENCE'
SF_TOKEN_URL = 'SF_TOKEN_URL'

class AuthEnv:
    def __init__(self, config):
        self.config = config

    def get_grant_type(self):
        return self.config.getenv(SF_GRANT_TYPE)

    def get_client_id(self):
        return self.config.getenv(SF_CLIENT_ID)

    def get_client_secret(self):
        return self.config.getenv(SF_CLIENT_SECRET)

    def get_username(self):
        return self.config.getenv(SF_USERNAME)

    def get_password(self):
        return self.config.getenv(SF_PASSWORD)

    def get_private_key(self):
        return self.config.getenv(SF_PRIVATE_KEY)

    def get_subject(self):
        return self.config.getenv(SF_SUBJECT)

    def get_audience(self):
        return self.config.getenv(SF_AUDIENCE)

    def get_token_url(self):
        return self.config.getenv(SF_TOKEN_URL)


class Auth:
    access_token = None
    instance_url = None
    # Never used, maybe in the future
    token_type = None

    def __init__(self, access_token: str, instance_url: str, token_type: str) -> None:
        self.access_token = access_token
        self.instance_url = instance_url
        self.token_type = token_type

    def get_access_token(self) -> str:
        return self.access_token

    def get_instance_url(self) -> str:
        return self.instance_url
