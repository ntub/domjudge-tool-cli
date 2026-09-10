from typing import Any, Self

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    last_login_time: str | None = None
    first_login_time: str | None = None
    team: str | None = None
    roles: list[str] = Field(default_factory=list)
    id: str
    username: str
    name: str
    email: EmailStr | None = None
    last_ip: str | None = None
    ip: str | None = None
    enabled: bool = True
    team_id: str | None = None
    affiliation: str | None = None
    password: str | None = None

    def update(self, **kwargs: Any) -> None:
        ignore_fields = {"id", "username", "team_id"}
        for key, value in kwargs.items():
            if key in ignore_fields:
                continue

            if hasattr(self, key):
                setattr(self, key, value)


class CreateUser(BaseModel):
    username: str
    name: str
    email: EmailStr | None = None
    password: str | None = None
    affiliation: str | None = None
    is_exist: bool | None = None

    @classmethod
    def from_user(cls, user: "User", **kwargs: Any) -> Self:
        user_info: dict[str, Any] = {"is_exist": True}
        user_dict = user.model_dump()
        if user_dict:
            user_info.update(user_dict)

        if kwargs:
            user_info.update(kwargs)

        return cls(**user_info)
