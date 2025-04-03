from dataclasses import dataclass

@dataclass
class Question:
    description: str
    required: bool
    prompt: str
    datatype: type