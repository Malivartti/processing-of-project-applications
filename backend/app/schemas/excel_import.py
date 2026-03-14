from pydantic import BaseModel


class ImportRowError(BaseModel):
    row: int
    field: str
    message: str


class ImportPreviewResponse(BaseModel):
    valid_count: int
    error_count: int
    errors: list[ImportRowError]
    duplicates: list[str]
