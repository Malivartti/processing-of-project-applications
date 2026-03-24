from pydantic import BaseModel

from app.schemas.project import ProjectRead


class CompareResponse(BaseModel):
    project_a: ProjectRead
    project_b: ProjectRead
    score: float | None
    keywords: list[str]
    highlight_tokens: list[str]
