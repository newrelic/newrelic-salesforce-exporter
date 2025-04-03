from .base import BaseModel

class EnvModel(BaseModel):
    end_date: str
    start_date: str

    def check(self):
        # No checks required
        return super().check()