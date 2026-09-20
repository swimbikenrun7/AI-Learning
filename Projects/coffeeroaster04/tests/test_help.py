"""The how-to page (/help): it is public, its links resolve, and what it says matches the app.

A tutorial goes stale silently, so these tests tie it to the app: the button and field labels
it names must exist in the templates and scripts, and the roast-level table must agree with
calculations.classify_roast.
"""

import re
import unittest
from itertools import pairwise
from pathlib import Path
from unittest import mock

import app
import calculations as calc

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
OWNER_EMAIL = "owner@example.com"


def read(relative):
    return (ROOT / relative).read_text()


def visible_text(html):
    """The page's words: no tags, no style blocks, entities and spacing normalised."""
    html = re.sub(r"<(style|script).*?</\1>", "", html, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&amp;", "&").replace("&#39;", "'").replace("&mdash;", "-")
    return re.sub(r"\s+", " ", text)


RENDER_ROASTERS = {
    "r": {
        "name": "Test Roaster",
        "values": {
            "profile_grid_minutes": 12,
            "has_temp_readout": True,
            "temp_unit": "F",
            "temp_min": 60,
            "temp_max": 500,
            "wizard": {
                "time_to_first_crack_s": {"low": 375, "medium": 375, "high": 405},
                "natural_time_adjust_s": 20,
                "dtr_by_level": {
                    "City Roast": 0.12,
                    "City Plus": 0.13,
                    "Full City": 0.16,
                    "Full City Plus": 0.18,
                    "Vienna Roast": 0.2,
                    "Italian Roast": 0.23,
                },
                "profile_start_temp": 315,
                "default_first_crack_temp": 400,
            },
        },
    }
}


class HelpTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        self.body = self.client.get("/help").get_data(as_text=True)
        self.text = visible_text(self.body)
        self.ids = set(re.findall(r'id="([\w-]+)"', self.body))


class TestThePage(HelpTestCase):
    def test_it_is_public(self):
        self.assertEqual(self.client.get("/help").status_code, 200)

    def test_it_is_available_to_a_logged_in_user_too(self):
        with self.client.session_transaction() as sess:
            sess["user_email"] = OWNER_EMAIL
        self.assertEqual(self.client.get("/help").status_code, 200)

    def test_every_contents_link_points_at_a_section_that_exists(self):
        toc = re.search(r'<nav class="help-toc".*?</nav>', self.body, re.DOTALL).group(
            0
        )
        targets = re.findall(r'href="#([\w-]+)"', toc)
        self.assertGreaterEqual(len(targets), 6)
        for target in targets:
            with self.subTest(section=target):
                self.assertIn(target, self.ids)

    def test_every_section_is_in_the_contents_and_has_a_heading(self):
        toc = re.search(r'<nav class="help-toc".*?</nav>', self.body, re.DOTALL).group(
            0
        )
        listed = re.findall(r'href="#([\w-]+)"', toc)
        sections = re.findall(
            r'<section class="help-section" id="([\w-]+)">\s*<h2>', self.body
        )
        self.assertEqual(sections, listed)

    def test_the_footer_links_to_it_on_public_pages(self):
        footer = self.client.get("/about").get_data(as_text=True)
        self.assertIn('<a href="/help">Help</a>', footer)

    def test_the_home_page_points_new_users_at_it(self):
        with self.client.session_transaction() as sess:
            sess["user_email"] = OWNER_EMAIL
        home = self.client.get("/").get_data(as_text=True)
        self.assertIn('<a href="/help">How to use Crackle</a>', home)

    def test_the_links_out_of_it_work(self):
        for url in re.findall(r'href="(/[\w-]+)"', self.body):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class TestContextualLinks(HelpTestCase):
    def test_every_help_link_in_a_template_points_at_a_section_that_exists(self):
        found = []
        for path in sorted(TEMPLATES.glob("*.html")):
            for anchor in re.findall(r'href="/help#([\w-]+)"', path.read_text()):
                found.append((path.name, anchor))
        self.assertGreaterEqual(len(found), 4)
        for name, anchor in found:
            with self.subTest(template=name, section=anchor):
                self.assertIn(anchor, self.ids)

    def test_the_key_pages_link_to_their_sections(self):
        expected = {
            "choose_roaster.html": ("profiles", "drip-espresso"),
            "profile_form.html": ("wizard",),
            "add_roast.html": ("logging",),
            "roast_detail.html": ("reading",),
        }
        for name, anchors in expected.items():
            source = (TEMPLATES / name).read_text()
            for anchor in anchors:
                with self.subTest(template=name, section=anchor):
                    self.assertIn(f'href="/help#{anchor}"', source)


class TestItMatchesTheApp(HelpTestCase):
    """Names in the how-to are checked against the app itself."""

    def test_the_home_menu_buttons(self):
        home = read("templates/home.html")
        for label in ("Add roast", "View roasts", "View and edit roast profiles"):
            with self.subTest(label=label):
                self.assertIn(f">{label}<", home)
                self.assertIn(label, self.text)

    def test_the_add_profile_button(self):
        self.assertIn("+ Add new profile", read("templates/profiles.html"))
        self.assertIn("+ Add new profile", self.text)

    def test_the_wizard_labels(self):
        form = read("templates/profile_form.html")
        for label in ("Want some help? Try the profile wizard", "Generate profile"):
            with self.subTest(label=label):
                self.assertIn(label, form)
                self.assertIn(label, self.text)

    def test_the_timer_and_first_crack_labels(self):
        template = read("templates/add_roast.html")
        script = read("static/js/add_roast_live.js")
        # Each label is looked for where the app actually writes it (a button's text, or a
        # quoted string in the script), so a word inside a longer name cannot satisfy it.
        labels = (
            ("Start", template, ">Start<"),
            ("Reset", template, ">Reset<"),
            ("First Crack Now!", template, ">First Crack Now!<"),
            ("Stop", script, 'textContent = "Stop"'),
            ("Pull in", script, '"Pull in "'),
            ("Pull now!", script, '"Pull now!"'),
        )
        for label, source, needle in labels:
            with self.subTest(label=label):
                self.assertIn(needle, source)
                self.assertIn(label, self.text)

    def test_the_add_roast_field_labels(self):
        form = read("templates/add_roast.html").lower()
        for label in (
            "date",
            "bean name",
            "start condition",
            "ambient temperature",
            "green weight",
            "total roast time",
            "finished weight",
        ):
            with self.subTest(label=label):
                self.assertIn(label, form)
                self.assertIn(label, self.text.lower())
        self.assertIn("Submit", read("templates/add_roast.html"))
        self.assertIn("Submit", self.text)

    def test_the_roast_page_and_list_labels(self):
        detail = read("templates/roast_detail.html")
        for label in (
            "Weight loss",
            "Classification",
            "Development time",
            "DTR",
            "Delete this roast",
        ):
            with self.subTest(label=label):
                self.assertIn(label, detail)
                self.assertIn(label, self.text)
        self.assertIn("Cupping notes", detail)
        self.assertIn("cupping notes", self.text)
        self.assertIn("Export CSV", read("templates/roasts.html"))
        self.assertIn("Export CSV", self.text)

    def test_the_style_names(self):
        for label in app.PROFILE_STYLES.values():
            with self.subTest(style=label):
                self.assertIn(label, self.text)

    def test_the_calibrated_roaster_it_names_is_the_one_in_the_data(self):
        from data_persistence import load_roasters

        calibrated = [
            roaster["name"]
            for roaster in load_roasters().values()
            if roaster["values"]["calibrated"]
        ]
        self.assertEqual(calibrated, ["Fresh Roast SR800"])
        self.assertIn("Fresh Roast SR800", self.text)

    def test_the_roast_level_table_agrees_with_classify_roast(self):
        table = re.search(r"<table>.*?</table>", self.body, re.DOTALL).group(0)
        rows = re.findall(r"<td>(.*?)</td><td>(.*?)</td>", table)
        self.assertEqual(len(rows), 6)
        # Every row's upper bound is where classify_roast moves to the next level.
        bounds = []
        for weight_loss, level in rows:
            numbers = [float(n) for n in re.findall(r"\d+\.\d+", weight_loss)]
            bounds.append((numbers[-1], level))
        for (bound, level), (_, next_level) in pairwise(bounds):
            with self.subTest(level=level):
                self.assertEqual(calc.classify_roast(bound - 0.005), level)
                self.assertEqual(calc.classify_roast(bound), next_level)
        self.assertEqual(calc.classify_roast(0), bounds[0][1])
        self.assertEqual(calc.classify_roast(30), bounds[-1][1])
        # The lower bound of each row equals the row above's upper bound.
        for (weight_loss, _), (bound, _) in zip(rows[1:], bounds):
            self.assertIn(f"{bound:.2f}%", weight_loss)

    def test_it_names_no_temperature_unit_symbol(self):
        # Units belong to the roaster (see the unit guard); the page uses words.
        self.assertNotRegex(self.body, r"(°|&deg;)\s*[FC]\b")


class TestTheLinksRender(unittest.TestCase):
    """The contextual links show up on the rendered pages, not just in the sources."""

    def setUp(self):
        self.profiles = {
            "p": {
                "name": "P",
                "roaster_id": "r",
                "temps": [300] + [None] * 11,
                "owner": OWNER_EMAIL,
            }
        }
        self.records = {
            "rec": {
                "date": "09/07/2026",
                "bean_name": "Bean",
                "green_weight": 150.0,
                "finished_weight": 128.0,
                "total_roast_time": 480,
                "time_of_first_crack": 375,
                "roast_profile_id": "p",
                "roaster_id": "r",
                "temp_unit": "F",
                "target_temps": [None] * 12,
                "actual_temps": [None] * 12,
                "owner": OWNER_EMAIL,
            }
        }
        for patcher in (
            mock.patch.object(app, "roast_profiles", self.profiles),
            mock.patch.object(app, "roast_records", self.records),
            mock.patch.object(app, "roasters", RENDER_ROASTERS),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user_email"] = OWNER_EMAIL

    def links(self, url):
        body = self.client.get(url).get_data(as_text=True)
        return set(re.findall(r'href="/help#([\w-]+)"', body))

    def test_the_roaster_chooser(self):
        self.assertEqual(self.links("/profiles/new"), {"profiles", "drip-espresso"})

    def test_the_profile_form_with_a_wizard(self):
        self.assertEqual(self.links("/profiles/new?roaster=r"), {"wizard"})

    def test_add_roast(self):
        self.assertEqual(self.links("/roasts/new/p"), {"logging"})

    def test_the_roast_page(self):
        self.assertEqual(self.links("/roasts/rec"), {"reading"})


if __name__ == "__main__":
    unittest.main()
