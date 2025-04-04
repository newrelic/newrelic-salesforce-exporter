from dataclasses import dataclass
from enum import Enum
from .prompt import prompt_list, prompt_int, prompt_bool, prompt_str

@dataclass
class Question:
    description: str
    required: bool
    prompt: str
    datatype: type = None

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

def ask_str(question: Question, checker) -> str:
    print_question(question)
    r = prompt_str(question.prompt, checker, question.required)
    print_response(r)

# Print formating

def print_response(r):
    print("-> Response =", r)

def print_question(question: Question):
    print(question.description + " (" + ("required" if question.required else "optional") + ")")