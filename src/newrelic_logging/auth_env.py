import os

class AuthEnv:
    SF_GRANT_TYPE = 'SF_GRANT_TYPE'
    SF_CLIENT_ID =  'SF_CLIENT_ID'
    SF_CLIENT_SECRET = 'SF_CLIENT_SECRET'
    SF_USERNAME = 'SF_USERNAME'
    SF_PASSWORD = 'SF_PASSWORD'
    SF_PRIVATE_KEY = 'SF_PRIVATE_KEY'
    SF_SUBJECT = 'SF_SUBJECT'
    SF_AUDIENCE = 'SF_AUDIENCE'
    NR_LICENSE_KEY = 'NR_LICENSE_KEY'
    NR_ACCOUNT_ID = 'NR_ACCOUNT_ID'

    def __init__(self, prefix):
        self.SF_GRANT_TYPE = prefix + self.SF_GRANT_TYPE
        self.SF_CLIENT_ID =  prefix + self.SF_CLIENT_ID
        self.SF_CLIENT_SECRET = prefix + self.SF_CLIENT_SECRET
        self.SF_USERNAME = prefix + self.SF_USERNAME
        self.SF_PASSWORD = prefix + self.SF_PASSWORD
        self.SF_PRIVATE_KEY = prefix + self.SF_PRIVATE_KEY
        self.SF_SUBJECT = prefix + self.SF_SUBJECT
        self.SF_AUDIENCE = prefix + self.SF_AUDIENCE
    
    def get_grant_type(self, default=None):
        return self.get(self.SF_GRANT_TYPE, default)
    
    def get_client_id(self, default=None):
        return self.get(self.SF_CLIENT_ID, default)
    
    def get_client_secret(self, default=None):
        return self.get(self.SF_CLIENT_SECRET, default)
    
    def get_username(self, default=None):
        return self.get(self.SF_USERNAME, default)
    
    def get_password(self, default=None):
        return self.get(self.SF_PASSWORD, default)
    
    def get_private_key(self, default=None):
        return self.get(self.SF_PRIVATE_KEY, default)
    
    def get_subject(self, default=None):
        return self.get(self.SF_SUBJECT, default)
    
    def get_audience(self, default=None):
        return self.get(self.SF_AUDIENCE, default)
    
    def get_license_key(self, default=None):
        return self.get(self.NR_LICENSE_KEY, default)
    
    def get_account_id(self, default=None):
        return self.get(self.NR_ACCOUNT_ID, default)

    def get(self, var_name, default):
        if default == None:
            # Can raise exception
            return os.environ[var_name]
        else:
            return os.environ.get(var_name, default)