"""
b64encode.py — binary-safe base64 encoding for Drive uploads.

Why this exists: reading a binary file (PDF/xlsx) via a text-mode method
(Python's open(path) without 'rb', PowerShell Get-Content without -Raw/-Encoding
Byte, cat in some shells) silently translates or drops bytes on Windows,
corrupting the file. This script ALWAYS opens in binary mode and writes its
output as a single stdout write, so there is no ambiguity for the routine to
get wrong.

Usage:
    python3 scripts/b64encode.py <path-to-file>

Prints ONLY the base64 string to stdout (no trailing newline inside the
encoded data itself, though the print call adds one at the very end — trim
if your Drive tool is strict about that).
"""
from __future__ import annotations
import base64
import sys


def main():
    if len(sys.argv) != 2:
        print("usage: python3 scripts/b64encode.py <path>", file=sys.stderr)
        return 1
    path = sys.argv[1]
    with open(path, "rb") as f:  # 'rb' is the whole point — never omit this
        data = f.read()
    encoded = base64.b64encode(data).decode("ascii")
    sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    sys.exit(main())
