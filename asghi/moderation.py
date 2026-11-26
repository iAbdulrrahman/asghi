import io
import wave
"""Content moderation and language compliance.
Enforces Requirements 18.1 (Fusha only), 18.2 (halal/appropriate content), 12 (upload limit), and 19 (1-3 min duration).
"""
import re
from typing import Tuple, List, Optional

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


# Arabic prefixes that may attach to a prohibited term without changing it
_PREFIXES = ("", "ال", "و", "وال", "بال", "كال", "فال", "لل", "ولل")


def _term_pattern(term: str) -> str:
    """Whole-word match that tolerates the usual Arabic proclitics.

    A plain substring test rejected legitimate words: the term "سب" occurs inside
    "النسبة" (the ratio) and "بسبب" (because).
    """
    prefix = "|".join(sorted(_PREFIXES, key=len, reverse=True))
    edge = r"[\w\u0600-\u06FF]"
    return rf"(?<!{edge})(?:{prefix}){re.escape(term)}(?!{edge})"


def check_content_guidelines(text: str) -> Tuple[bool, str]:
    """Req 18.2: Enforce content guidelines excluding vulgar, inappropriate, or non-halal material."""
    if not text or not text.strip():
        return False, "المحتوى فارغ."

    for term in PROHIBITED_TERMS:
        if re.search(_term_pattern(term), text):
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


def _wav_duration(file_bytes: bytes) -> Optional[float]:
    try:
        with wave.open(io.BytesIO(file_bytes), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0 and frames > 0:
                return round(frames / float(rate), 2)
    except Exception:
        return None
    return None


# MPEG audio frame tables (version 1 & 2, layer III is what phones produce)
_BITRATE_V1L3 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
_BITRATE_V2L3 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160]
_RATES_V1 = [44100, 48000, 32000]
_RATES_V2 = [22050, 24000, 16000]
_RATES_V25 = [11025, 12000, 8000]


def _mp3_duration(file_bytes: bytes) -> Optional[float]:
    """Count MPEG audio frames and derive duration; works for CBR and VBR."""
    i = 0
    if file_bytes[:3] == b"ID3" and len(file_bytes) > 10:
        size = (
            (file_bytes[6] & 0x7F) << 21
            | (file_bytes[7] & 0x7F) << 14
            | (file_bytes[8] & 0x7F) << 7
            | (file_bytes[9] & 0x7F)
        )
        i = 10 + size

    frames = 0
    seconds = 0.0
    while i + 4 <= len(file_bytes):
        if file_bytes[i] != 0xFF or (file_bytes[i + 1] & 0xE0) != 0xE0:
            i += 1
            continue
        version_bits = (file_bytes[i + 1] >> 3) & 0x03      # 3=MPEG1, 2=MPEG2, 0=MPEG2.5
        layer_bits = (file_bytes[i + 1] >> 1) & 0x03        # 1=Layer III
        bitrate_idx = (file_bytes[i + 2] >> 4) & 0x0F
        rate_idx = (file_bytes[i + 2] >> 2) & 0x03
        if layer_bits != 1 or bitrate_idx in (0, 15) or rate_idx == 3:
            i += 1
            continue
        table = _BITRATE_V1L3 if version_bits == 3 else _BITRATE_V2L3
        rates = _RATES_V1 if version_bits == 3 else (_RATES_V2 if version_bits == 2 else _RATES_V25)
        bitrate = table[bitrate_idx] * 1000
        rate = rates[rate_idx]
        samples = 1152 if version_bits == 3 else 576
        padding = (file_bytes[i + 2] >> 1) & 0x01
        frame_len = int((samples // 8) * bitrate / rate) + padding
        if frame_len <= 4:
            i += 1
            continue
        frames += 1
        seconds += samples / float(rate)
        i += frame_len
    if frames:
        return round(seconds, 2)
    return None


def _mp4_duration(file_bytes: bytes) -> Optional[float]:
    """Read the mvhd box of an MP4/M4A container (version 0 and 1)."""
    idx = file_bytes.find(b"mvhd")
    if idx < 0 or idx + 8 > len(file_bytes):
        return None
    p = idx + 4
    version = file_bytes[p]
    try:
        if version == 0:
            timescale = int.from_bytes(file_bytes[p + 12:p + 16], "big")
            duration = int.from_bytes(file_bytes[p + 16:p + 20], "big")
        else:
            timescale = int.from_bytes(file_bytes[p + 20:p + 24], "big")
            duration = int.from_bytes(file_bytes[p + 24:p + 32], "big")
    except IndexError:
        return None
    if timescale:
        return round(duration / float(timescale), 2)
    return None


def extract_audio_duration(file_bytes: bytes) -> Optional[float]:
    """Parse duration in seconds from WAV, MP3 or MP4/M4A. None when unreadable."""
    for parser in (_wav_duration, _mp4_duration, _mp3_duration):
        value = parser(file_bytes)
        if value:
            return value
    return None


def validate_audio_metadata(file_size_bytes: int, duration_seconds: float) -> Tuple[bool, str]:
    """NFR 12 & 19: Check upload limit (25 MB) and duration guidelines (60-180 seconds)."""
    max_bytes = 25 * 1024 * 1024  # 25 MB
    if file_size_bytes > max_bytes:
        return False, "حجم الملف يتجاوز الحد الأقصى المسموح به (25 ميغابايت)."

    if duration_seconds < 60.0:
        return False, "مدة التسجيل قصيرة جداً (الهدف الأساسي 60 إلى 180 ثانية)."
    if duration_seconds > 180.0:
        return False, "مدة التسجيل تتجاوز الحد الأقصى المسموح به (180 ثانية)."

    return True, ""
