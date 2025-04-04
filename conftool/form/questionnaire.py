from conftool.model.api_endpoint import ApiEndpointModel
from .question import Question, ask_int, ask_enum, ask_bool, ask_str, ask_any

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
        description="A whole word with no spaces",
        required=True,
        prompt="Word?"),
        word_check)
    ask_any(Question(
        description="Just put anything here",
        required=True,
        prompt="String?"))
    
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
        description="A whole word with no spaces",
        required=False,
        prompt="Word?"),
        word_check)
    ask_any(Question(
        description="Just put anything here",
        required=False,
        prompt="String?"))

#TODO: custom error message when checker fails

def word_check(text: str) -> bool:
    return not (' ' in text)