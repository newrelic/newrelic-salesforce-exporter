from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt

def prompt_list(message: str, options: list[str], required: bool) -> int:
    for i,option in enumerate(options):
        print(str(i+1) + ") " + str(option))
    validator = ListNumberValidator(1, len(options), not required)
    response = prompt(message + " ", validator=validator)
    if response is None or response == "":
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
    
def prompt_str(message: str, checker, required: bool) -> int:
    validator = StringValidator(checker, not required)
    response = prompt(message + " ", validator=validator)
    if response == "":
        return None
    else:
        return response

def prompt_any(message: str, required: bool) -> int:
    validator = SkippableValidator(not required)
    response = prompt(message + " ", validator=validator)
    if response == "":
        return None
    else:
        return response

class SkippableValidator(Validator):
    skippable: bool

    def __init__(self, skippable: bool):
        self.skippable = skippable
        super().__init__()

    def validate(self, document):
        text = document.text
        if not self.skippable and (text is None or text == ""):
            raise ValidationError(
                message=f"Input can't be empty",
                cursor_position=0
            )
        
    def can_skip(self, text):
        return self.skippable and (text is None or text == "")

class ListNumberValidator(SkippableValidator):
    min: int
    max: int

    def __init__(self, min: int, max: int, skippable: bool):
        super().__init__(skippable)
        self.min = min
        self.max = max

    def validate(self, document):
        super().validate(document)
        text = document.text
        if self.can_skip(text):
            return
        if not self.digit_in_range(text):
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

class NumberRangeValidator(SkippableValidator):
    min: int
    max: int

    def __init__(self, min: int, max: int, skippable: bool):
        super().__init__(skippable)
        self.min = min
        self.max = max

    def validate(self, document):
        super().validate(document)
        text = document.text
        if self.can_skip(text):
            return
        if not self.number_in_range(text):
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
        
class BooleanValidator(SkippableValidator):
    def validate(self, document):
        super().validate(document)
        text = document.text
        if self.can_skip(text):
            return
        if text not in {"y", "Y", "n", "N"}:
            raise ValidationError(
                message=f"Input must be a 'Y', 'y', 'N' or 'n'",
                cursor_position=0
            )
        
class StringValidator(SkippableValidator):
    checker: None

    def __init__(self, checker, skippable: bool):
        super().__init__(skippable)
        self.checker = checker

    def validate(self, document):
        super().validate(document)
        text = document.text
        if self.can_skip(text):
            return
        if not self.checker(text):
            raise ValidationError(
                message=f"Wrong format",
                cursor_position=0
            )