from conftool.model.api_endpoint import ApiEndpointModel
from .question import Question, ask_int, ask_enum, ask_bool, ask_str

def run():
    print("REQUIRED")
    
    ask_enum(Question(
        description="New Relic API endpoint",
        required=True,
        prompt="API Endpoint (1-3)?",
        datatype=ApiEndpointModel))
    ask_int(Question(
        description="Redis server port number",
        required=True,
        prompt="Port (0-65535)?"),
        0, 65535)
    ask_bool(Question(
        description="Enable cache for event deduplication",
        required=True,
        prompt="Cache enabled (y/n)?"))
    ask_str(Question(
        description="A simple string with nothing else",
        required=True,
        prompt="String?"),
        checker)
    
    print("OPTIONAL")

    ask_enum(Question(
        description="New Relic API endpoint",
        required=False,
        prompt="API Endpoint (1-3)?",
        datatype=ApiEndpointModel))
    ask_int(Question(
        description="Redis server port number",
        required=False,
        prompt="Port (0-65535)?"),
        0, 65535)
    ask_bool(Question(
        description="Enable cache for event deduplication",
        required=False,
        prompt="Cache enabled (y/n)?"))
    ask_str(Question(
        description="A simple string with nothing else",
        required=False,
        prompt="String?"),
        checker)

#TODO: custom error message when checker fails

def checker(text: str) -> bool:
    return True