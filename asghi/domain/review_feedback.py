"""ReviewFeedback class.
Matches class-diagram.puml and sequence diagram 2.
"""
from __future__ import annotations
from typing import Optional


class ReviewFeedback:
    def __init__(
        self,
        isFusha: bool,
        dialectFree: Optional[bool] = None,
        audioQuality: Optional[int] = None,
        feedback: str = "",
    ):
        self.isFusha: bool = isFusha
        self.dialectFree: Optional[bool] = dialectFree
        self.audioQuality: Optional[int] = audioQuality
        self.feedback: str = feedback
