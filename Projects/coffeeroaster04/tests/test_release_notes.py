"""The app's version and release notes: the data file, its loader, the footer, and /whats-new."""

import json
import re
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import app
import data_persistence

ROOT = Path(__file__).resolve().parents[1]
NOTES_PATH = ROOT / "data" / "release_notes.json"
VERSION = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
MAX_CHANGE_LENGTH = 220  # release notes are a condensed summary, not the developer log

NOTES = [
    {
        "version": "2.1.0",
        "date": "2026-10-05",
        "title": "Newest thing",
        "changes": ["Added the newest thing.", "Fixed <b>bold</b> handling."],
    },
    {
        "version": "2.0.0",
        "date": "2026-09-19",
        "title": "Older thing",
        "changes": ["Added the older thing."],
    },
]


def version_key(version):
    return tuple(int(part) for part in version.split("."))


class TestReleaseNotesFile(unittest.TestCase):
    def setUp(self):
        self.notes = json.loads(NOTES_PATH.read_text())

    def test_it_has_releases(self):
        self.assertGreaterEqual(len(self.notes), 1)

    def test_each_release_has_exactly_the_expected_fields(self):
        for release in self.notes:
            with self.subTest(version=release.get("version")):
                self.assertEqual(
                    sorted(release), ["changes", "date", "title", "version"]
                )

    def test_versions_are_major_minor_patch_numbers(self):
        for release in self.notes:
            with self.subTest(version=release["version"]):
                self.assertRegex(release["version"], VERSION)

    def test_releases_are_newest_first_with_strictly_rising_versions(self):
        versions = [version_key(release["version"]) for release in self.notes]
        self.assertEqual(versions, sorted(versions, reverse=True))
        self.assertEqual(len(versions), len(set(versions)))

    def test_dates_are_real_and_never_older_than_the_release_before(self):
        dates = [date.fromisoformat(release["date"]) for release in self.notes]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_each_release_has_a_title_and_short_plain_changes(self):
        for release in self.notes:
            with self.subTest(version=release["version"]):
                self.assertTrue(release["title"].strip())
                self.assertGreaterEqual(len(release["changes"]), 1)
                for change in release["changes"]:
                    self.assertIsInstance(change, str)
                    self.assertEqual(change, change.strip())
                    self.assertTrue(change)
                    self.assertLessEqual(len(change), MAX_CHANGE_LENGTH)
                    self.assertNotIn("<", change)

    def test_the_project_version_is_the_newest_release(self):
        # Plain text, not tomllib: PythonAnywhere runs Python 3.10, which has no tomllib.
        pyproject = (ROOT / "pyproject.toml").read_text()
        match = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
        self.assertEqual(match.group(1), self.notes[0]["version"])

    def test_the_apps_version_is_the_newest_release(self):
        body = app.app.test_client().get("/about").get_data(as_text=True)
        self.assertIn(f"v{self.notes[0]['version']} &middot; What", body)


class TestLoader(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "release_notes.json"
        patcher = mock.patch.object(data_persistence, "RELEASE_NOTES_PATH", self.path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_missing_file_means_no_releases(self):
        self.assertEqual(data_persistence.load_release_notes(), [])

    def test_it_reads_the_file(self):
        self.path.write_text(json.dumps(NOTES))
        self.assertEqual(data_persistence.load_release_notes(), NOTES)

    def test_a_corrupted_file_stops_the_program_and_is_left_alone(self):
        self.path.write_text("[not json")
        with self.assertRaises(SystemExit) as stopped:
            data_persistence.load_release_notes()
        self.assertEqual(stopped.exception.code, 1)
        self.assertEqual(self.path.read_text(), "[not json")


class TestWhatsNewPage(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(app, "release_notes", NOTES)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = app.app.test_client()

    def test_it_is_public(self):
        response = self.client.get("/whats-new")
        self.assertEqual(response.status_code, 200)

    def test_it_lists_every_release_newest_first_with_its_changes(self):
        body = self.client.get("/whats-new").get_data(as_text=True)
        self.assertLess(body.index("Version 2.1.0"), body.index("Version 2.0.0"))
        for text in ("Newest thing", "Older thing", "Added the older thing."):
            self.assertIn(text, body)

    def test_dates_are_written_out_without_zero_padding(self):
        body = self.client.get("/whats-new").get_data(as_text=True)
        self.assertIn("October 5, 2026", body)
        self.assertIn("September 19, 2026", body)

    def test_only_the_newest_release_is_marked_current(self):
        body = self.client.get("/whats-new").get_data(as_text=True)
        self.assertEqual(body.count("current version"), 1)
        self.assertLess(body.index("current version"), body.index("Version 2.0.0"))

    def test_note_text_is_escaped(self):
        body = self.client.get("/whats-new").get_data(as_text=True)
        self.assertIn("&lt;b&gt;bold&lt;/b&gt;", body)
        self.assertNotIn("<b>bold</b>", body)

    def test_with_no_releases_it_says_so(self):
        with mock.patch.object(app, "release_notes", []):
            body = self.client.get("/whats-new").get_data(as_text=True)
        self.assertIn("No release notes yet.", body)

    def test_the_date_formatter(self):
        self.assertEqual(app.format_release_date("2026-09-05"), "September 5, 2026")
        self.assertEqual(app.format_release_date("2027-12-31"), "December 31, 2027")


class TestFooter(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def footer(self, url="/about"):
        body = self.client.get(url).get_data(as_text=True)
        return re.search(
            r'<footer class="site-footer">(.*?)</footer>', body, re.DOTALL
        ).group(1)

    def test_it_shows_the_newest_version_and_links_to_whats_new(self):
        with mock.patch.object(app, "release_notes", NOTES):
            footer = self.footer()
        self.assertIn('<a href="/whats-new">v2.1.0 &middot; What', footer)
        self.assertIn('<a href="/about">About</a>', footer)

    def test_the_version_follows_the_newest_entry(self):
        newer = [{**NOTES[0], "version": "9.9.9"}] + NOTES
        with mock.patch.object(app, "release_notes", newer):
            self.assertIn("v9.9.9", self.footer())

    def test_it_is_on_pages_a_logged_in_user_sees_too(self):
        with self.client.session_transaction() as sess:
            sess["user_email"] = "someone@example.com"
        with mock.patch.object(app, "release_notes", NOTES):
            self.assertIn("v2.1.0", self.footer("/"))

    def test_with_no_releases_the_footer_has_no_version(self):
        with mock.patch.object(app, "release_notes", []):
            footer = self.footer()
        self.assertNotIn("whats-new", footer)
        self.assertIn("About", footer)


if __name__ == "__main__":
    unittest.main()
