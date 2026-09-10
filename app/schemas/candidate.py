from pydantic import BaseModel


class CandidateExtractResponse(BaseModel):
    name: str | None
    email: str | None
    phone: str | None
    skills: list[str]