from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class RSVPIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    will_attend: bool
    companion_full_name: str | None = Field(default=None, min_length=2, max_length=120)
    companion_will_attend: bool | None = None

    @model_validator(mode="after")
    def validate_companion(self) -> "RSVPIn":
        has_name = bool(self.companion_full_name and self.companion_full_name.strip())
        has_attendance = self.companion_will_attend is not None
        if has_name != has_attendance:
            raise ValueError(
                "Для спутника нужно указать и ФИО, и ответ приду/не приду"
            )
        return self


class RSVPStored(RSVPIn):
    created_at: datetime


class RSVPOut(BaseModel):
    status: str = "ok"
    message: str = "Спасибо. Ваш ответ отправлен."
