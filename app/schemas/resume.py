from datetime import datetime

from pydantic import BaseModel


class ResumeResponse(BaseModel):

    id: int
    file_name: str
    file_path: str
    uploaded_at: datetime

    model_config = {
        "from_attributes": True
    }


class ParsedResumeResponse(BaseModel):

    filename: str
    extracted_text: str