import uuid
from typing import Annotated
from uuid import UUID as UserID

from annotated_types import MaxLen, MinLen
from pydantic import BaseModel, ConfigDict


class UserSchema(BaseModel):
    model_config = ConfigDict(strict=True)

    user_id: UserID
    username: str
    hashed_password: str


class UserCreateSchema(BaseModel):
    user_id: UserID = uuid.uuid4()
    username: Annotated[str, MinLen(3), MaxLen(20)]
    password: str


class UserUpdateSchema(BaseModel):
    username: Annotated[str, MinLen(3), MaxLen(20)]
    old_password: str
    new_password: str
