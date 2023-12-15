import os

class AuthEnv:
    GRANT_TYPE = 'SF_GRANT_TYPE'
    CLIENT_ID =  'SF_CLIENT_ID'
    CLIENT_SECRET = 'SF_CLIENT_SECRET'
    USERNAME = 'SF_USERNAME'
    PASSWORD = 'SF_PASSWORD'
    PRIVATE_KEY = 'SF_PRIVATE_KEY'
    SUBJECT = 'SF_SUBJECT'
    AUDIENCE = 'SF_AUDIENCE'

    def __init__(self, prefix):
        self.GRANT_TYPE = prefix + self.GRANT_TYPE
        self.CLIENT_ID =  prefix + self.CLIENT_ID
        self.CLIENT_SECRET = prefix + self.CLIENT_SECRET
        self.USERNAME = prefix + self.USERNAME
        self.PASSWORD = prefix + self.PASSWORD
        self.PRIVATE_KEY = prefix + self.PRIVATE_KEY
        self.SUBJECT = prefix + self.SUBJECT
        self.AUDIENCE = prefix + self.AUDIENCE
    
    def get_grant_type(self, default=None):
        return self.get(self.GRANT_TYPE, default)
    
    def get_client_id(self, default=None):
        return self.get(self.CLIENT_ID, default)
    
    def get_client_secret(self, default=None):
        return self.get(self.CLIENT_SECRET, default)
    
    def get_username(self, default=None):
        return self.get(self.USERNAME, default)
    
    def get_password(self, default=None):
        return self.get(self.PASSWORD, default)
    
    def get_private_key(self, default=None):
        return self.get(self.PRIVATE_KEY, default)
    
    def get_subject(self, default=None):
        return self.get(self.SUBJECT, default)
    
    def get_audience(self, default=None):
        return self.get(self.AUDIENCE, default)

    def get(self, var_name, default):
        if default == None:
            # Can raise exception
            return os.environ[var_name]
        else:
            return os.environ.get(var_name, default)