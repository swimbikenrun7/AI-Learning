"""Every page carries the viewport tag, so a phone lays it out at its own width.

Without <meta name="viewport"> a phone assumes a 980 px page and shrinks it, and none of the
responsive CSS applies. All pages inherit it from base.html; the browser check
(tests/browser) measures the phone layout itself.
"""

import unittest
from pathlib import Path

import app

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"
VIEWPORT_TAG = '<meta name="viewport" content="width=device-width, initial-scale=1">'


class TestViewportTag(unittest.TestCase):
    def test_the_base_template_sets_the_viewport(self):
        self.assertIn(VIEWPORT_TAG, (TEMPLATES / "base.html").read_text())

    def test_every_page_template_extends_the_base(self):
        # A page that did not would render at desktop width on a phone. Files starting
        # with an underscore are fragments included into pages.
        pages = [
            path
            for path in sorted(TEMPLATES.glob("*.html"))
            if path.name != "base.html" and not path.name.startswith("_")
        ]
        self.assertGreater(len(pages), 5)
        for path in pages:
            with self.subTest(template=path.name):
                self.assertIn('{% extends "base.html" %}', path.read_text())

    def test_served_pages_carry_the_tag(self):
        client = app.app.test_client()
        for url in ("/about", "/login", "/signup"):
            with self.subTest(url=url):
                self.assertIn(VIEWPORT_TAG, client.get(url).get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
