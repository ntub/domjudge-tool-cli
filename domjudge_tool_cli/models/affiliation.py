from pydantic import BaseModel


class Affiliation(BaseModel):
    id: str | None = None
    shortname: str
    name: str
    country: str
    team_affiliation: str | None = None
