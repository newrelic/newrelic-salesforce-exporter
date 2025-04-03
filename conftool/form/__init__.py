from .question import Question
from conftool.model.api_endpoint import ApiEndpointModel

def run_form():
    r = Question(
        prompt="API Endpoint?",
        description="New Relic API endpoint",
        datatype=ApiEndpointModel,
        required=True
        ).run()
    print("-> Response =", r.value)
