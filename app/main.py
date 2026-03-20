from datetime import datetime
from typing import Annotated

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException
from pydantic import ValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.email_service import send_rsvp_email
from app.schemas import RSVPIn, RSVPOut, RSVPStored
from app.settings import get_mail_settings
from app.storage import save_one


app = FastAPI(
    title="Wedding RSVP API",
    version="1.0.0",
    description="API для приема ответов RSVP анкеты.",
)

TRUTHY_VALUES = {"1", "true", "yes", "on", "да"}
FALSY_VALUES = {"0", "false", "no", "off", "нет"}


def _to_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in TRUTHY_VALUES:
        return True
    if lowered in FALSY_VALUES:
        return False
    return None


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _save_rsvp(payload: RSVPIn) -> RSVPStored:
    data = RSVPStored(**payload.model_dump(), created_at=datetime.utcnow())
    save_one(data.model_dump(mode="json"))
    return data

# Enable CORS so an existing frontend can call the API from another origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/rsvp", response_model=RSVPOut, tags=["rsvp"])
def create_rsvp_form(
    background_tasks: BackgroundTasks,
    name: Annotated[str, Form(min_length=2, max_length=120)],
    will_attend: Annotated[str | None, Form()] = None,
    attendance: Annotated[str | None, Form()] = None,
    companion_name: Annotated[str | None, Form()] = None,
    companion_will_attend: Annotated[str | None, Form()] = None,
    companion_attendance: Annotated[str | None, Form()] = None,
) -> RSVPOut:
    parsed_attendance = _to_bool(will_attend)
    if parsed_attendance is None:
        parsed_attendance = _to_bool(attendance)

    if parsed_attendance is None:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["form", "will_attend"],
                    "msg": "Укажите will_attend: true/false (или yes/no)",
                    "type": "value_error.attendance",
                }
            ],
        )

    cleaned_companion_name = _clean_text(companion_name)
    parsed_companion_attendance = _to_bool(companion_will_attend)
    if parsed_companion_attendance is None:
        parsed_companion_attendance = _to_bool(companion_attendance)

    has_companion_name = cleaned_companion_name is not None
    has_companion_attendance = parsed_companion_attendance is not None
    if has_companion_name != has_companion_attendance:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["form", "companion"],
                    "msg": "Для спутника укажите и ФИО, и ответ приду/не приду",
                    "type": "value_error.companion",
                }
            ],
        )

    try:
        payload = RSVPIn(
            full_name=name.strip(),
            will_attend=parsed_attendance,
            companion_full_name=cleaned_companion_name,
            companion_will_attend=parsed_companion_attendance,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    saved_data = _save_rsvp(payload)
    background_tasks.add_task(send_rsvp_email, saved_data, get_mail_settings())
    return RSVPOut()
