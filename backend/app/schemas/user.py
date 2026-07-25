from pydantic import BaseModel, Field, field_validator

from app.schemas.common import Page


class RoleOut(BaseModel):
    id: int
    name: str
    description: str | None = None


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    roles: list[RoleOut] = []


class UserListOut(Page):
    items: list[UserOut]


class UserCreateIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise ValueError("邮箱不能为空")
        return value


class UserStatusUpdateIn(BaseModel):
    is_active: bool


class UserSetRolesIn(BaseModel):
    role_ids: list[int] = Field(default_factory=list)


class UserBatchStatusIn(BaseModel):
    user_ids: list[int] = Field(min_length=1)
    is_active: bool


class UserBatchRolesIn(BaseModel):
    user_ids: list[int] = Field(min_length=1)
    role_ids: list[int] = Field(default_factory=list)
