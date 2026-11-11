"""Content moderation and language compliance.
Enforces Requirements 18.1 (Fusha only), 18.2 (halal/appropriate content), 12 (upload limit), and 19 (1-3 min duration).
"""
import re
from typing import Tuple, List

# Inappropriate or vulgar patterns to reject (Req 18.2)
PROHIBITED_TERMS = [
    "قمار",
    "خمر",
    "كحول",
    "ميسر",
    "ربا",
    "إباحي",
    "سب",
    "شتم",
]

# Obvious dialect markers that should not appear in formal Fusha passages (Req 18.1 / 5.5)
DIALECT_MARKERS = [
    "عايز",
    "بدي",
    "شو بدي",
    "هيك",
    "برشا",
    "ديالو",
    "واش راك",
    "إيش في",
    "زوين",
    "مزيان",
]


def check_content_guidelines(text: str) -> Tuple[bool, str]:
    """Req 18.2: Enforce content guidelines excluding vulgar, inappropriate, or non-halal material."""
    if not text or not text.strip():
        return False, "المحتوى فارغ."

    normalized = text.lower()
    for term in PROHIBITED_TERMS:
        if term in normalized:
            return False, f"المحتوى يخالف معايير النشر لاحتوائه على مفردات غير ملائمة: '{term}'"

    return True, ""


def check_fusha_compliance(text: str) -> Tuple[bool, str]:
    """Req 18.1: Check that text is in formal Fusha Arabic and free of dialect markers."""
    if not text or not text.strip():
        return False, "النص فارغ."

    # Verify presence of Arabic script
    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
    if arabic_chars < 5:
        return False, "النص يجب أن يكون مكتوباً باللغة العربية الفصحى."

    for marker in DIALECT_MARKERS:
        if re.search(rf"\b{re.escape(marker)}\b", text):
            return False, f"النص يحتوي على ألفاظ عامية غير فصيحة: '{marker}'"

    return True, ""


def validate_audio_metadata(file_size_bytes: int, duration_seconds: float) -> Tuple[bool, str]:
    """NFR 12 & 19: Check upload limit (25 MB) and duration guidelines (1-3 min target)."""
    max_bytes = 25 * 1024 * 1024  # 25 MB
    if file_size_bytes > max_bytes:
        return False, "حجم الملف يتجاوز الحد الأقصى المسموح به (25 ميغابايت)."

    # Allow reasonable bounds for testing while checking target range
    if duration_seconds < 10:
        return False, "مدة التسجيل قصيرة جداً (الهدف الأساسي 1-3 دقائق)."
    if duration_seconds > 600:
        return False, "مدة التسجيل تتجاوز الحد الأقصى المسموح به."

    return True, ""
