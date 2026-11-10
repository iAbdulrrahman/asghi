"""Domain enumerations for اصغِ (Asghi).
Matches class-diagram.puml exactly.
"""
from enum import Enum


class UserRole(str, Enum):
    LEARNER = "LEARNER"
    CONTRIBUTOR = "CONTRIBUTOR"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"


class Difficulty(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class Level(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class Origin(str, Enum):
    AI = "AI"
    HUMAN = "HUMAN"


class AttributionType(str, Enum):
    SHOW_NAME = "SHOW_NAME"
    ANONYMOUS = "ANONYMOUS"


class QuestionType(str, Enum):
    MCQ = "MCQ"
    TRUE_FALSE = "TRUE_FALSE"
    FILL_IN_BLANK = "FILL_IN_BLANK"
    SHORT_ANSWER = "SHORT_ANSWER"


class ContentStatus(str, Enum):
    DRAFT = "DRAFT"
    CLAIMED = "CLAIMED"
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    FLAGGED = "FLAGGED"


class FlagStatus(str, Enum):
    PENDING = "PENDING"
    NO_ACTION = "NO_ACTION"
    ACTION_TAKEN = "ACTION_TAKEN"
