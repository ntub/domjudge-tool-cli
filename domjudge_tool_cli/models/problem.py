from pydantic import BaseModel


class Problem(BaseModel):
    ordinal: int
    id: str
    short_name: str
    label: str
    time_limit: int
    externalid: str
    name: str
    rgb: str | None = None
    color: str | None = None
    test_data_count: int


class ProblemItem(BaseModel):
    id: str
    time_limit: int
    test_data_count: int
    name: str
    export_file_path: str | None = None
