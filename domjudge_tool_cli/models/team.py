from pydantic import BaseModel


class Team(BaseModel):
    group_ids: list[str]
    affiliation: str | None = None
    nationality: str | None = None
    id: str
    icpc_id: str | None = None
    name: str
    display_name: str | None = None
    organization_id: str | None = None
    members: str | None = None
