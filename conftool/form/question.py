from dataclasses import dataclass
from conftool.model.enum import ConfigEnum
from .prompt import prompt_list, prompt_int, prompt_bool, prompt_str, prompt_any
from .text import Text

@dataclass
class Question:
    text: Text
    required: bool
    datatype: type = None

def ask_enum(question: Question) -> ConfigEnum:
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

def ask_dict(question: Question, key_checker, val_checker) -> dict[str,str]:
    print_question(question)
    k = prompt_str("Key?", key_checker, question.required)
    if k == None:
        return None
    v = prompt_str("Value?", val_checker, True)
    res = {k:v}
    while True:
        k = prompt_str("Key (empty to finish)?", key_checker, False)
        if k == None:
            break
        v = prompt_str("Value?", val_checker, True)
        res[k] = v
    return res

# Print formating

def print_response(r):
    #print("-> Response =", r)
    print()

def print_question(question: Question):
    print_path()
    print(Color.BG_BLUE + Color.FG_BOLD_WHITE + question.text.desc + Color.RESET + "\n")
    print("REQUIRED" if question.required else "OPTIONAL")
    print()

def print_warning(warning: str):
    print(Color.BG_YELLOW + Color.FG_BOLD_BLACK + "!! " + warning + " !!" + Color.RESET + "\n")

# Question hierarchy

_question_path: list[str] = []

def push_level(level: str):
    _question_path.append(level)

def pop_level():
    _question_path.pop()

def print_path():
    print(Color.BG_RED + Color.FG_BOLD_WHITE + " @ " + " > ".join(_question_path) + ' ' + Color.RESET + '\n')

class Color:
    BG_RED = '\x1b[41m'
    FG_BOLD_RED = '\x1b[1;31m'

    FG_BOLD_WHITE = '\x1b[1;37m'

    BG_BLUE = '\x1b[44m'

    BG_YELLOW = '\x1b[43m'

    FG_BOLD_BLACK = '\x1b[1;30m'

    RESET = '\x1b[0m'