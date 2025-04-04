from dataclasses import dataclass
from enum import Enum
from conftool.model.api_endpoint import ApiEndpointModel
from .prompt import prompt_enum

@dataclass
class Question:
    description: str
    required: bool
    prompt: str
    datatype: type

def run():
    r = ask(Question(
        description="New Relic API endpoint",
        required=True,
        prompt="API Endpoint?",
        datatype=ApiEndpointModel))
    print_response(r)

#TODO: function to check constrains (URL format, cron format, etc)
#TODO: custom error message when checker fails

def ask(question: Question) -> any:
    print_question(question)
    if issubclass(question.datatype, Enum):
        return ask_enum(question)
    #TODO: support all possible data types

def ask_enum(question: Question) -> any:
    options = [e.value for e in question.datatype]
    response = prompt_enum(question.prompt, options, question.required)
    if response == "":
        return None
    else:
        number = int(response)
    return question.datatype(options[number - 1])

def print_response(r):
    print("-> Response =", r)

def print_question(question):
    print(question.description + " (" + ("required" if question.required else "optional") + ")")