"""Exercise exact finding ignores without weakening the scanner."""

import json
import secrets
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FindingIgnores(unittest.TestCase):
    def test_only_the_exact_historical_finding_is_ignored(self):
        policy = (ROOT / ".betterleaksignore").read_text()
        manifest = json.loads((ROOT / ".github/source-tools.json").read_text())
        asset = next(
            item
            for item in manifest["assets"]
            if item["repository"] == "betterleaks/betterleaks"
        )
        version = subprocess.check_output(["betterleaks", "version"], text=True).strip()
        self.assertEqual(version, asset["tag"].removeprefix("v"))

        with tempfile.TemporaryDirectory(prefix="template-scanner-") as folder:
            work = Path(folder)

            def git(*args):
                return subprocess.check_output(
                    [
                        "git",
                        "-c",
                        "user.name=CI fixture",
                        "-c",
                        "user.email=ci@example.invalid",
                        *args,
                    ],
                    cwd=work,
                    text=True,
                ).strip()

            def content():
                key = "POSTGRES_PASSWORD"
                return f"{key}={secrets.token_hex(24)}\n"

            def scan():
                report = work / "report.json"
                report.unlink(missing_ok=True)
                result = subprocess.run(
                    [
                        "betterleaks",
                        "git",
                        "--no-banner",
                        "--redact",
                        "--report-format",
                        "json",
                        "--report-path",
                        str(report),
                        ".",
                    ],
                    cwd=work,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertIn(result.returncode, (0, 1), result.stderr)
                if result.returncode:
                    self.assertTrue(report.is_file())
                findings = json.loads(report.read_text()) if report.exists() else []
                self.assertEqual(bool(findings), result.returncode == 1)
                return findings

            git("init", "-q")
            (work / "first.env").write_text(content())
            (work / "second.env").write_text(content())
            git("add", "first.env", "second.env")
            git("commit", "-qm", "test: add synthetic scanner controls")
            (work / ".betterleaksignore").write_text(policy)
            before = scan()
            self.assertEqual(
                {item["File"] for item in before}, {"first.env", "second.env"}
            )

            first = {
                item["Fingerprint"] for item in before if item["File"] == "first.env"
            }
            second = {
                item["Fingerprint"] for item in before if item["File"] == "second.env"
            }
            (work / ".betterleaksignore").write_text(
                policy + "\n".join(sorted(first)) + "\n"
            )
            remaining = scan()
            self.assertEqual({item["Fingerprint"] for item in remaining}, second)

            (work / ".betterleaksignore").write_text(
                policy + "\n".join(sorted(first | second)) + "\n"
            )
            self.assertEqual(scan(), [])
            (work / "first.env").write_text(content())
            git("add", "first.env")
            git("commit", "-qm", "test: add a new finding outside historical ignores")
            current = scan()
            self.assertTrue(current)
            self.assertEqual({item["File"] for item in current}, {"first.env"})
            self.assertFalse(
                {item["Fingerprint"] for item in current}.intersection(first | second)
            )


if __name__ == "__main__":
    unittest.main()
