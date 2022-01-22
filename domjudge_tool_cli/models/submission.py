from typing import Dict, List, Optional

from pydantic import BaseModel


class Submission(BaseModel):
    language_id: Optional[str]
    time: Optional[str]
    contest_time: Optional[str]
    id: str
    externalid: Optional[str]
    team_id: str
    problem_id: str
    entry_point: Optional[str]
    files: Optional[List[Dict[str, str]]]
    submission_id: Optional[str]
    filename: Optional[str]
    source: Optional[str]


class SubmissionFile(BaseModel):
    id: str
    submission_id: Optional[str]
    filename: Optional[str]
    source: Optional[str]
