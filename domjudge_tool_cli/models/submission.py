from pydantic import BaseModel


class Submission(BaseModel):
    language_id: str | None = None
    time: str | None = None
    contest_time: str | None = None
    id: str
    externalid: str | None = None
    team_id: str
    problem_id: str
    entry_point: str | None = None
    files: list[dict[str, str]] | None = None
    submission_id: str | None = None
    filename: str | None = None
    source: str | None = None


class SubmissionFile(BaseModel):
    id: str
    submission_id: str | None = None
    filename: str | None = None
    source: str | None = None
