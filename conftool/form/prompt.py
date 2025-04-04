from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt

def prompt_enum(message: str, options: list[str], required: bool) -> str:
    # Print list
    for i,option in enumerate(options):
        print(str(i+1) + ") " + str(option))
    validator = ListNumberValidator(1, len(options), not required)
    return prompt(message + " ", validator=validator)
    
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