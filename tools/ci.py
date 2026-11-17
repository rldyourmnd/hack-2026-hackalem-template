"""Run the existing native verification with job-owned database cleanup."""

import signal
import subprocess


def stop(signum, _frame):
    raise SystemExit(128 + signum)


def main():
    signal.signal(signal.SIGTERM, stop)
    try:
        subprocess.run(["just", "setup"], check=True)
        subprocess.run(["just", "verify"], check=True)
    finally:
        subprocess.run(["docker", "compose", "down", "-v"], check=True)


if __name__ == "__main__":
    main()
