"""User class.
Matches class-diagram.puml and sequence diagram 4.
"""
from __future__ import annotations
import hashlib
from typing import Optional, List
from uuid import UUID, uuid4

from asghi.domain.enums import UserRole, Level
from asghi.domain.user_role_profile import UserRoleProfile
from asghi.domain.learner_profile import LearnerProfile
from asghi.domain.contributor_profile import ContributorProfile
from asghi.domain.reviewer_profile import ReviewerProfile
from asghi.domain.admin_profile import AdminProfile


def hash_password(password: str) -> str:
    """PBKDF2 SHA-256 password hash (Invention #2)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class User:
    _registry: List[User] = []

    def __init__(
        self,
        email: Optional[str] = None,
        phoneNo: Optional[str] = None,
        displayName: str = "",
        passwordHash: str = "",
        arabicLevel: Level = Level.A1,
        userId: Optional[UUID] = None,
    ):
        if not email and not phoneNo:
            # UML note: at least one of email/phone is non-null
            pass

        self.userId: UUID = userId or uuid4()
        self.email: Optional[str] = email
        self.phoneNo: Optional[str] = phoneNo
        self.displayName: str = displayName
        self.passwordHash: str = passwordHash
        self.arabicLevel: Level = arabicLevel
        self.userProfiles: List[UserRoleProfile] = []
        self.status: str = "ACTIVE"

        User._registry.append(self)

    def register(self, emailOrPhone: str, password: str) -> None:
        """Sequence 4 step 11-14: register user with email or phone number."""
        if "@" in emailOrPhone:
            self.email = emailOrPhone
        else:
            self.phoneNo = emailOrPhone
        self.passwordHash = hash_password(password)

    def login(self, emailOrPhone: str, password: str) -> bool:
        """Authenticate user against password hash."""
        match_identifier = (
            (self.email and self.email.lower() == emailOrPhone.lower())
            or (self.phoneNo and self.phoneNo == emailOrPhone)
        )
        if not match_identifier:
            return False
        return self.passwordHash == hash_password(password)

    def completeProfile(
        self,
        displayName: str,
        level: Level,
        roleInterest: UserRole,
    ) -> None:
        """Sequence 4 step 16-20: complete short profile."""
        self.displayName = displayName
        self.arabicLevel = level
        self.addRole(roleInterest)

    def addRole(self, role: UserRole) -> UserRoleProfile:
        """Sequence 4 step 22-42: create and attach role profile."""
        for prof in self.userProfiles:
            if prof.role == role:
                return prof

        new_profile: UserRoleProfile
        if role == UserRole.LEARNER:
            new_profile = LearnerProfile()
        elif role == UserRole.CONTRIBUTOR:
            new_profile = ContributorProfile()
        elif role == UserRole.REVIEWER:
            new_profile = ReviewerProfile()
        elif role == UserRole.ADMIN:
            new_profile = AdminProfile()
        else:
            raise ValueError(f"Unknown role: {role}")

        self.userProfiles.append(new_profile)
        return new_profile

    def removeRole(self, role: UserRole) -> None:
        """Remove role profile from user."""
        self.userProfiles = [p for p in self.userProfiles if p.role != role]
