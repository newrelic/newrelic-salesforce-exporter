class Query:
    query = None
    env = None

    def __init__(self, query) -> None:
        if type(query) == dict:
            self.query = query.get("query", "")
            query.pop('query', None)
            self.env = query
        elif type(query) == str:
            self.query = query
            self.env = {}

    def get_query(self) -> str:
        return self.query
    
    def set_query(self, query: str) -> None:
        self.query = query
    
    def get_env(self) -> dict:
        return self.env
    