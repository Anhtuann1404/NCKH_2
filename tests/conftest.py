"""Pytest configuration and shared fixtures for NCKH_2.

Guarantees clean test execution on any clean checkout (macOS, Linux, Windows),
with graceful fallback if system temp directory runs low on disk space.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_TMP = PROJECT_ROOT / "tmp"

# Check if system temporary directory has insufficient disk space (e.g. 0 bytes on Windows C:)
# If so, redirect temporary file creation to project-local tmp directory on D:
try:
    temp_dir = tempfile.gettempdir()
    free_space = shutil.disk_usage(temp_dir).free
    if free_space < 100 * 1024 * 1024:  # less than 100MB
        LOCAL_TMP.mkdir(parents=True, exist_ok=True)
        os.environ["TMPDIR"] = str(LOCAL_TMP)
        os.environ["TEMP"] = str(LOCAL_TMP)
        os.environ["TMP"] = str(LOCAL_TMP)
        tempfile.tempdir = str(LOCAL_TMP)
except Exception:
    pass
