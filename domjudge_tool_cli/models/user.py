from datetime import datetime
from typing import List, Optional

from pydantic import (
    BaseModel,
    EmailStr,
    IPvAnyAddress,
)


class User(BaseModel):
    last_login_time: Optional[datetime]
    first_login_time: Optional[datetime]
    team: Optional[str]
    roles: List[str]
    id: str
    username: str
    name: str
    email: Optional[EmailStr]
    last_ip: Optional[IPvAnyAddress]
    ip: Optional[IPvAnyAddress]
    enabled: bool
    team_id: Optional[str]