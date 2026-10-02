"""Exercise real archive rejection boundaries without application/database state."""

import hashlib
import json
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from release import validate, validate_policy, verify
from repository_hygiene import check_public_file, check_public_path


class PublicArchiveTests(unittest.TestCase):
    def archive(self, folder, entries, *, manifest_commit="a" * 40, zip_commit="a" * 40):
        archive = folder / "candidate.zip"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(archive, "w") as file:
                file.comment = zip_commit.encode()
                for name, data in entries:
                    file.writestr(name, data)
        manifest = {
            "archive": archive.name,
            "commit": manifest_commit,
            "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "files": {name: hashlib.sha256(data).hexdigest() for name, data in entries},
        }
        (folder / "manifest.json").write_text(json.dumps(manifest))
        return archive

    def test_private_paths_and_cross_platform_traversal_are_refused(self):
        for name in [
            "../dump.txt",
            "C:/dump.txt",
            r"folder\dump.txt",
            ".ENV",
            ".local/fixture.json",
            "public/private.key",
            "database.sqlite3",
            "backup.sql.gz",
            "apps/web/dist/index.html",
            ".local-audit.json",
            "test-results/trace.zip",
            "certificates/server.pem",
        ]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                check_public_path(name)

    def test_public_configuration_and_source_are_allowed(self):
        check_public_file(".env.example", b"POSTGRES_PASSWORD=GENERATE_MIGRATOR_PASSWORD")
        check_public_file("apps/api/migrations/versions/0007_product_operations.py", b"# DDL")
        check_public_file("docs/architecture/diagrams/containers.svg", b"<svg/>")

    def test_secret_detection_does_not_disclose_the_value(self):
        secret = b"ghp_" + b"A" * 40
        with self.assertRaises(ValueError) as error:
            check_public_file("innocent.txt", secret)
        self.assertIn("innocent.txt", str(error.exception))
        self.assertNotIn(secret.decode(), str(error.exception))

    def test_zip_commit_must_match_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            self.archive(folder, [("README.md", b"public")], zip_commit="b" * 40)
            with self.assertRaisesRegex(ValueError, "Archive commit disagrees"):
                verify(folder)

    def test_manifest_archive_path_is_checked_before_reading(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / "manifest.json").write_text(json.dumps({"archive": r"..\private.zip"}))
            with self.assertRaises(ValueError):
                verify(folder)

    def test_duplicate_zip_entries_are_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            self.archive(folder, [("README.md", b"first"), ("README.md", b"last")])
            with self.assertRaisesRegex(ValueError, "Duplicate candidate"):
                verify(folder)

    def test_secret_in_zip_is_refused_even_with_matching_checksums(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            secret = b"-----BEGIN " + b"PRIVATE KEY-----\nsynthetic rejected payload"
            self.archive(folder, [("innocent.txt", secret)])
            with self.assertRaisesRegex(ValueError, "Possible secret in innocent.txt"):
                verify(folder)

    def test_changed_zip_cannot_pass_the_original_checksum(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            archive = self.archive(folder, [("README.md", b"public")])
            with archive.open("ab") as file:
                file.write(b"tampered")
            with self.assertRaisesRegex(ValueError, "Candidate archive checksum mismatch"):
                verify(folder)


class PortfolioPolicyTests(unittest.TestCase):
    def metadata(self):
        return json.loads(
            (Path(__file__).resolve().parents[1] / "docs/release/candidate.json").read_text()
        )

    def test_stable_portfolio_delegates_publication_to_github(self):
        candidate = self.metadata()
        validate_policy(candidate)
        self.assertIsNone(candidate["stable_release_published"])

    def test_cannot_claim_publication_before_external_receipt(self):
        candidate = self.metadata()
        candidate["stable_release_published"] = True
        with self.assertRaisesRegex(ValueError, "external GitHub receipt"):
            validate_policy(candidate)

    def test_cannot_grant_commercial_production(self):
        candidate = self.metadata()
        candidate["production_ready"] = True
        with self.assertRaisesRegex(ValueError, "production readiness"):
            validate_policy(candidate)

    def test_historical_rc_policy_still_supported(self):
        candidate = self.metadata()
        candidate.update(
            version="3.0.0-rc.1",
            python_version="3.0.0rc1",
            status="candidate_for_review",
            stable_release_published=False,
        )
        validate_policy(candidate)

    def test_historical_media_cannot_be_redated_as_stable(self):
        root = Path(__file__).resolve().parents[1]

        def read(name):
            data = (root / name).read_bytes()
            if name == "docs/case/media/capture.json":
                capture = json.loads(data)
                capture["version"] = "3.0.0"
                return json.dumps(capture).encode()
            return data

        with self.assertRaisesRegex(ValueError, "recording evidence"):
            validate(read)


if __name__ == "__main__":
    unittest.main()
