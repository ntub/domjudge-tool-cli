from pydantic import BaseModel


class Judgement(BaseModel):
    judgement_type_id: str | None = None
    judgehost: str | None = None
    valid: bool
    submission_id: str
    id: str
    end_contest_time: str | None = None
    end_time: str | None = None
    start_contest_time: str | None = None
    start_time: str | None = None
    max_run_time: float | None = None
