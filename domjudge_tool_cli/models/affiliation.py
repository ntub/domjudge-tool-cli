from typing import Optional

from pydantic import BaseModel


class Affiliation(BaseModel):
    id: Optional[str]
    shortname: str
    name: str
    country: str
    team_affiliation: Optional[str]
