from dataclasses import dataclass
from enum import Enum
from .prompt import prompt_list, prompt_int, prompt_bool, prompt_str, prompt_any
from .text import Text

@dataclass
class Question:
    text: Text
    required: bool
    datatype: type = None

def ask_enum(question: Question) -> Enum:
    print_question(question)
    options = [e._name_ for e in question.datatype]
    values = [e.value for e in question.datatype]
    num = prompt_list(question.text.prom, options, question.required)
    if num is None:
        r = None
    else:
        r = question.datatype(values[num - 1])
    print_response(r)
    return r

def ask_int(question: Question, min: int, max: int) -> int:
    print_question(question)
    r = prompt_int(question.text.prom, min, max, question.required)
    print_response(r)
    return r

def ask_bool(question: Question) -> bool:
    print_question(question)
    r = prompt_bool(question.text.prom, question.required)
    print_response(r)
    return r

def ask_str(question: Question, checker) -> str:
    print_question(question)
    r = prompt_str(question.text.prom, checker, question.required)
    print_response(r)
    return r

def ask_any(question: Question) -> str:
    print_question(question)
    r = prompt_any(question.text.prom, question.required)
    print_response(r)
    return r

# Print formating

def print_response(r):
    print("-> Response =", r)
    print()

def print_question(question: Question):
    print(question.text.desc)
    print("Required." if question.required else "Optional.")
    print()