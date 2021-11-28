from typing import List, Optional

from pydantic import (
    BaseModel,
)

class Problem(BaseModel):
    ordinal: int
    id: str
    short_name: str
    label: str
    time_limit: int
    externalid: str
    name: str
    rgb: str
    color: str
    test_data_count: int
