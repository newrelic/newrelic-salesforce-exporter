from dataclasses import dataclass
from enum import Enum
from conftool.model.api_endpoint import ApiEndpointModel
from .prompt import prompt_list, prompt_int, prompt_bool

@dataclass
class Question:
    description: str
    required: bool
    prompt: str
    datatype: type = None

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

# Ask for user responses

def ask_enum(question: Question) -> Enum:
    print_question(question)
    options = [e.value for e in question.datatype]
    num = prompt_list(question.prompt, options, question.required)
    if num is None:
        r = None
    else:
        r = question.datatype(options[num - 1])
    print_response(r)
    return r

def ask_int(question: Question, min: int, max: int) -> int:
    print_question(question)
    r = prompt_int(question.prompt, min, max, question.required)
    print_response(r)
    return r

def ask_bool(question: Question) -> bool:
    print_question(question)
    r = prompt_bool(question.prompt, question.required)
    print_response(r)

# Print formating

def print_response(r):
    print("-> Response =", r)

def print_question(question: Question):
    print(question.description + " (" + ("required" if question.required else "optional") + ")")