from conftool.model.api_endpoint import ApiEndpointModel
from .question import Question
from .runner import ask

def questionnaire():
    r = ask(Question(
        description="New Relic API endpoint",
        required=True,
        prompt="API Endpoint?",
        datatype=ApiEndpointModel))
    print("-> Response =", r)
