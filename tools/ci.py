"""Run native verification and security with job-owned database cleanup."""

import signal
import subprocess
import sys


def stop(signum, _frame):
    raise SystemExit(128 + signum)


def main():
    signal.signal(signal.SIGTERM, stop)
    application_status = 125
    security_status = 125
    cleanup_status = 125
    try:
        application_status = subprocess.run(["just", "setup"], check=False).returncode
        if application_status == 0:
            application_status = subprocess.run(
                ["just", "verify-application"], check=False
            ).returncode
        security_status = subprocess.run(["just", "security"], check=False).returncode
    finally:
        cleanup_status = subprocess.run(
            ["docker", "compose", "down", "-v"], check=False
        ).returncode
    return application_status or security_status or cleanup_status


if __name__ == "__main__":
    sys.exit(main())
