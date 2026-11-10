"""UserRoleProfile abstract class.
Matches class-diagram.puml.
"""
from __future__ import annotations
from abc import ABC
from typing import Optional
from uuid import UUID, uuid4

from asghi.domain.enums import UserRole


class UserRoleProfile(ABC):
    def __init__(
        self,
        role: UserRole,
        userRoleProfileId: Optional[UUID] = None,
    ):
        self.userRoleProfileId: UUID = userRoleProfileId or uuid4()
        self.role: UserRole = role
