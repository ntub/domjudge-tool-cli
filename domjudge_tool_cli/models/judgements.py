from typing import Optional

from pydantic import BaseModel


class Judgement(BaseModel):
    """
    {
    "max_run_time": 0.102,
    "start_time": "2022-04-22T09:18:39.362+08:00",
    "start_contest_time": "0:08:39.362",
    "end_time": "2022-04-22T09:18:42.700+08:00",
    "end_contest_time": "0:08:42.700",
    "id": "13070",
    "submission_id": "12653",
    "valid": true,
    "judgehost": "judgehost-4-4",
    "judgement_type_id": "AC"
    }
    """

    judgement_type_id: Optional[str]
    judgehost: Optional[str]
    valid: bool
    submission_id: str
    id: str
    end_contest_time: Optional[str] = None
    end_time: Optional[str] = None
    start_contest_time: Optional[str] = None
    start_time: Optional[str] = None
    max_run_time: Optional[float] = None
