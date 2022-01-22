from typing import List, Optional

from pydantic import BaseModel


class Team(BaseModel):
    group_ids: List[str]
    affiliation: Optional[str]
    nationality: Optional[str]
    id: str
    icpc_id: Optional[str]
    name: str
    display_name: Optional[str]
    organization_id: Optional[str]
    members: Optional[str]
