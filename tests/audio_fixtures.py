"""Shared audio fixtures: a stream whose duration can actually be measured."""


def make_mp3(seconds: float) -> bytes:
    """MPEG-1 Layer III, 128 kbps, 44.1 kHz: 417-byte frames, 26.12 ms each.

    The old fixtures were bare frame headers with no payload, which no duration parser
    can time - and which a strict validator now rejects on purpose.
    """
    frame = b"\xff\xfb\x90\x64" + b"\x00" * 413
    frames = max(1, int(round(seconds / (1152 / 44100))))
    return frame * frames
