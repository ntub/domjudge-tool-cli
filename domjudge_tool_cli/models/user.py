from typing import List, Optional

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    last_login_time: Optional[str]
    first_login_time: Optional[str]
    team: Optional[str]
    roles: List[str]
    id: str
    username: str
    name: str
    email: Optional[EmailStr]
    last_ip: Optional[str]
    ip: Optional[str]
    enabled: bool
    team_id: Optional[str]


class CreateUser(BaseModel):
    username: str
    name: str
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    affiliation: Optional[str] = None
