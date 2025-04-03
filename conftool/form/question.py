from dataclasses import dataclass
from enum import Enum
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt

@dataclass
class Question:
    prompt: str
    description: str
    datatype: type
    required: bool

    def run(self) -> any:
        print(self.description + " (" + ("required" if self.required else "optional") + ")")
        if issubclass(self.datatype, Enum):
            return self._run_enum()
        #TODO: support all possible data types
    
    def _run_enum(self) -> any:
        options = [e.value for e in self.datatype]
        for i,e in enumerate(self.datatype):
            print(str(i+1) + ") " + str(e.value))
        number = int(prompt(self.prompt + " ", validator=ListNumberValidator(1, len(options))))
        #TODO: skippable if optional
        return self.datatype(options[number - 1])
    
    #TODO: function to check constrains (URL format, cron format, etc)
    #TODO: custom error message when checker fails
    
class ListNumberValidator(Validator):
    min: int
    max: int

    def __init__(self, min, max):
        self.min = min
        self.max = max
        super().__init__()

    def validate(self, document):
        text = document.text
        if text and not self.number_in_range(text):
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