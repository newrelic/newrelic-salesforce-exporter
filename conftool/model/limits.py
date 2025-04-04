from .base import BaseModel
from .api_ver import ApiVerModel

class LimitsModel(BaseModel):
    api_ver: ApiVerModel
    names: list[str]
    event_type: str

    def check(self):
        # No checks required
        super().check()