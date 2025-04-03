from enum import Enum
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt
from .question import Question

def ask(question: Question) -> any:
    print(question.description + " (" + ("required" if question.required else "optional") + ")")
    if issubclass(question.datatype, Enum):
        return ask_enum(question)
    #TODO: support all possible data types

def ask_enum(question: Question) -> any:
    options = [e.value for e in question.datatype]
    # Print list
    for i,e in enumerate(question.datatype):
        print(str(i+1) + ") " + str(e.value))
    response = prompt(question.prompt + " ", validator=ListNumberValidator(1, len(options), not question.required))
    if response == "":
        return None
    else:
        number = int(response)
    return question.datatype(options[number - 1])

#TODO: function to check constrains (URL format, cron format, etc)
#TODO: custom error message when checker fails
    
class ListNumberValidator(Validator):
    min: int
    max: int
    skippable: bool

    def __init__(self, min: int, max: int, skippable: bool):
        self.min = min
        self.max = max
        self.skippable = skippable
        super().__init__()

    def validate(self, document):
        text = document.text
        if not self.number_in_range(text):
            if self.skippable and text == "":
                return
            raise ValidationError(
                message="Input must be a number in the list",
                cursor_position=0
            )
    
    def number_in_range(self, text: str) -> bool:
        if text.isdigit():
            n = int(text)
            return n >= self.min and n <= self.max
        else:
            return False