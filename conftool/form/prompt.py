from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt

def prompt_list(message: str, options: list[str], required: bool) -> int:
    for i,option in enumerate(options):
        print(str(i+1) + ") " + str(option))
    validator = ListNumberValidator(1, len(options), not required)
    response = prompt(message + " ", validator=validator)
    if response is None:
        return None
    else:
        return int(response)
    
def prompt_int(message: str, min: int, max: int, required: bool) -> int:
    validator = NumberRangeValidator(min, max, not required)
    response = prompt(message + " ", validator=validator)
    if response is None or response == "":
        return None
    else:
        return int(response)
    
def prompt_bool(message: str, required: bool) -> int:
    validator = BooleanValidator(not required)
    response = prompt(message + " ", validator=validator)
    if response is None or response == "":
        return None
    else:
        return response == "y" or response == "Y"

    
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
        if not self.digit_in_range(text):
            if self.skippable and text == "":
                return
            raise ValidationError(
                message="Input must be a number in the list",
                cursor_position=0
            )
    
    def digit_in_range(self, text: str) -> bool:
        if text.isdigit():
            n = int(text)
            return n >= self.min and n <= self.max
        else:
            return False
        
class NumberRangeValidator(Validator):
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
                message=f"Input must be a number in the range [{self.min},{self.max}]",
                cursor_position=0
            )
    
    def number_in_range(self, text: str) -> bool:
        if text.isdecimal():
            n = int(text)
            return n >= self.min and n <= self.max
        else:
            return False
        
class BooleanValidator(Validator):
    skippable: bool

    def __init__(self, skippable: bool):
        self.skippable = skippable
        super().__init__()

    def validate(self, document):
        text = document.text
        if text not in {"y", "Y", "n", "N"}:
            if self.skippable and text == "":
                return
            raise ValidationError(
                message=f"Input must be a 'Y', 'y', 'N' or 'n'",
                cursor_position=0
            )