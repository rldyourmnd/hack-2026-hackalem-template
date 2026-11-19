"""Refuse the same generated-contract drift as the original CI job."""

import subprocess
import sys

status = subprocess.check_output(
    [
        "git",
        "status",
        "--porcelain",
        "--",
        "contracts/openapi.json",
        "frontend/src/shared/api/generated",
    ],
    text=True,
)
if status:
    print(
        "Generated contract or client differs from the accepted source:",
        file=sys.stderr,
    )
    print(status, file=sys.stderr, end="")
    raise SystemExit(1)
