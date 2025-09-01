#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Ensure we can import the package optimus_project_mcp when run as a script
REPO_ROOT = Path(__file__).resolve().parents[2]
SYS_PKG_PATH = REPO_ROOT / "mcp_servers"
if str(SYS_PKG_PATH) not in sys.path:
    sys.path.insert(0, str(SYS_PKG_PATH))

from optimus_project_mcp.indexer import Indexer  # type: ignore  # noqa: E402
from optimus_project_mcp.validator import Validator  # type: ignore  # noqa: E402


def read_staged_diff() -> str:
    try:
        out = subprocess.check_output(["git", "diff", "--cached", "-U0"], text=True)
        return out
    except Exception:
        return ""


def main() -> int:
    # Read diff from stdin if provided, else from staged changes
    if sys.stdin and not sys.stdin.isatty():
        diff_text = sys.stdin.read()
    else:
        diff_text = read_staged_diff()

    indexer = Indexer()
    indexer.refresh()
    validator = Validator(indexer.get_policy())
    result = validator.validate_diff(diff_text or "")

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
