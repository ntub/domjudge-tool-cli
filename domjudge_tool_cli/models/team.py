from typing import List, Optional

from pydantic import (
    BaseModel,
)


class Team(BaseModel):
    group_ids: List[str]
    affiliation: str
    nationality: str
    id: str
    icpc_id: Optional[str]
    name: str
    display_name: str
    organization_id: str
    members: Optional[str]
