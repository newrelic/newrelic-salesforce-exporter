from conftool.model.api_endpoint import ApiEndpointModel
from .question import Question, ask_int, ask_enum, ask_bool

def run():
    ask_enum(Question(
        description="New Relic API endpoint",
        required=True,
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


#TODO: function to check constrains (URL format, cron format, etc)
#TODO: custom error message when checker fails