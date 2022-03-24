from typing import Any, Dict, List, Optional

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
    affiliation: Optional[str] = None
    password: Optional[str] = None

    def update(self, **kwargs: Dict[str, Any]):
        ignore_fields = {"id", "username", "team_id"}
        for key, value in kwargs.items():
            if key in ignore_fields:
                continue

            if hasattr(self, key):
                setattr(self, key, value)


class CreateUser(BaseModel):
    username: str
    name: str
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    affiliation: Optional[str] = None
    is_exist: Optional[bool] = None

    @classmethod
    def from_user(cls, user: "User", **kwargs: Dict[str, Any]):
        user_info = dict(is_exist=True)
        if user.dict():
            user_info.update(user.dict())

        if kwargs:
            user_info.update(kwargs)

        return cls(**user_info)
