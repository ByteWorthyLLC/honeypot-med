"""Tiny standard-library PNG card renderer for offline report bundles."""

from __future__ import annotations

import binascii
import struct
import zlib
from pathlib import Path

from .launchkit import bundle_verdict


FONT: dict[str, tuple[str, ...]] = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("10010", "10010", "10010", "11111", "00010", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01111", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "11110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ":": ("00000", "00100", "00100", "00000", "00100", "00100", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
}


Color = tuple[int, int, int]


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", binascii.crc32(kind + data) & 0xFFFFFFFF)


def _encode_png(width: int, height: int, pixels: bytearray) -> bytes:
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * stride : (y + 1) * stride])
    return b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)) + _png_chunk(
        b"IDAT", zlib.compress(bytes(raw), 9)
    ) + _png_chunk(b"IEND", b"")


class Canvas:
    def __init__(self, width: int, height: int, bg: Color) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray(bg * (width * height))

    def rect(self, x: int, y: int, w: int, h: int, color: Color) -> None:
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        for yy in range(y0, y1):
            offset = (yy * self.width + x0) * 3
            for _ in range(x0, x1):
                self.pixels[offset : offset + 3] = bytes(color)
                offset += 3

    def text(self, x: int, y: int, text: str, color: Color, *, scale: int = 4, max_chars: int | None = None) -> None:
        value = text.upper()
        if max_chars is not None:
            value = value[:max_chars]
        cursor = x
        for char in value:
            glyph = FONT.get(char, FONT[" "])
            for row, pattern in enumerate(glyph):
                for col, pixel in enumerate(pattern):
                    if pixel == "1":
                        self.rect(cursor + col * scale, y + row * scale, scale, scale, color)
            cursor += 6 * scale

    def to_png(self) -> bytes:
        return _encode_png(self.width, self.height, self.pixels)


def _survival_label(report: dict) -> str:
    challenge = report.get("challenge")
    if isinstance(challenge, dict) and challenge.get("score_label"):
        return str(challenge["score_label"])
    events = list(report.get("events", []))
    survived = 0
    for event in events:
        severity = str(event.get("severity", "low")).lower()
        if int(event.get("proven_count", 0)) == 0 and severity not in {"high", "critical"}:
            survived += 1
    return f"{survived}/{len(events)} survived"


def build_social_card_png(report: dict, *, title: str, source_label: str) -> bytes:
    canvas = Canvas(1200, 630, (246, 239, 227))
    canvas.rect(0, 0, 1200, 630, (246, 239, 227))
    canvas.rect(0, 0, 760, 630, (255, 248, 234))
    canvas.rect(760, 0, 440, 630, (31, 38, 48))
    canvas.rect(56, 58, 150, 10, (200, 71, 45))
    canvas.text(56, 92, "HONEYPOT MED", (95, 102, 110), scale=4)
    canvas.text(56, 164, title, (31, 38, 48), scale=9, max_chars=22)
    canvas.text(56, 258, "PROMPT TRAP REPORT", (31, 38, 48), scale=6)
    canvas.text(56, 350, _survival_label(report), (200, 71, 45), scale=8, max_chars=20)
    canvas.text(56, 452, bundle_verdict(report), (31, 38, 48), scale=7, max_chars=16)
    canvas.text(56, 552, source_label, (95, 102, 110), scale=3, max_chars=44)
    canvas.rect(824, 76, 270, 270, (200, 71, 45))
    canvas.rect(862, 114, 194, 194, (246, 239, 227))
    canvas.rect(900, 152, 118, 118, (31, 38, 48))
    canvas.text(832, 410, "CASEBOOK", (246, 239, 227), scale=6)
    canvas.text(832, 486, "NO API KEYS", (246, 239, 227), scale=5)
    return canvas.to_png()


def build_badge_png(report: dict) -> bytes:
    canvas = Canvas(520, 92, (31, 38, 48))
    canvas.rect(0, 0, 220, 92, (31, 38, 48))
    canvas.rect(220, 0, 300, 92, (200, 71, 45))
    canvas.text(22, 30, "HONEYPOT MED", (246, 239, 227), scale=4)
    canvas.text(246, 30, _survival_label(report), (255, 248, 234), scale=4, max_chars=16)
    return canvas.to_png()


def write_png_card_artifacts(report: dict, outdir: str, *, title: str, source_label: str) -> dict:
    target = Path(outdir)
    target.mkdir(parents=True, exist_ok=True)
    social_path = target / "social-card.png"
    badge_path = target / "badge.png"
    social_path.write_bytes(build_social_card_png(report, title=title, source_label=source_label))
    badge_path.write_bytes(build_badge_png(report))
    return {"social_card_png": str(social_path), "badge_png": str(badge_path)}
