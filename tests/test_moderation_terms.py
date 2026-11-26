"""Moderation terms and audio metadata: no false positives, no client-trusted duration."""
from asghi.moderation import (
    check_content_guidelines,
    extract_audio_duration,
    validate_audio_metadata,
)


def test_legitimate_words_containing_a_prohibited_substring_are_accepted():
    # "سب" is a listed term; it also sits inside "النسبة" and "بسبب"
    for text in ["ارتفعت النسبة في المئة", "كان ذلك بسبب الطقس", "نص عربي عادي عن العلم"]:
        ok, msg = check_content_guidelines(text)
        assert ok, f"rejected legitimate text {text!r}: {msg}"


def test_prohibited_terms_are_still_caught_with_prefixes():
    for text in ["هذا قمار", "القمار حرام", "والخمر ممنوع", "الربا محرم"]:
        ok, msg = check_content_guidelines(text)
        assert not ok, f"missed prohibited text {text!r}"


def test_empty_text_is_rejected():
    assert not check_content_guidelines("")[0]
    assert not check_content_guidelines("   ")[0]


def test_mp3_duration_is_measured_from_frames():
    frame = b"\xff\xfb\x90\x64" + b"\x00" * 413          # 26.12 ms per frame
    duration = extract_audio_duration(frame * int(round(90 / (1152 / 44100))))
    assert duration is not None
    assert 85 <= duration <= 95, duration


def test_unreadable_audio_has_no_duration():
    assert extract_audio_duration(b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\x00" * 100) is None


def test_duration_bounds():
    assert validate_audio_metadata(1000, 5.0)[0] is False
    assert validate_audio_metadata(1000, 90.0)[0] is True
    assert validate_audio_metadata(1000, 400.0)[0] is False
    assert validate_audio_metadata(30 * 1024 * 1024, 90.0)[0] is False
