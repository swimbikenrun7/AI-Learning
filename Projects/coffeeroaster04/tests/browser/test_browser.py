"""Browser check: the chart, timer, wizard, and roaster-driven pages, in real headless Chromium.

There are no JavaScript tests, and the JavaScript is where a roaster's unit, row count, and
chart opening finally reach the screen, so this runs the real app on fixture data and drives
its pages: it loads them, clicks Start / First Crack Now! / Reset and the wizard, and checks
the chart data, axis titles, readouts, and that the console stayed clean.

It needs Chromium (or Chrome) and Node 22+ on the PATH, and network access for the Chart.js
CDN tag the pages use. When any of those is missing the tests are skipped with the reason.
No npm packages are used. Set SKIP_BROWSER_TESTS=1 to skip it on purpose.

Run just this check:  pytest tests/browser -rs
"""

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

from data_persistence import load_roasters

HERE = Path(__file__).resolve().parent
CHART_JS_URL = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.5.1/chart.umd.min.js"
BROWSER_NAMES = (
    "chromium",
    "chromium-browser",
    "google-chrome",
    "google-chrome-stable",
    "chrome",
)
OWNER = "owner@example.com"
CLOCK = r"^0:0[1-4]$"  # the timer has been running for a few seconds at most


def find_browser():
    for name in BROWSER_NAMES:
        path = shutil.which(name)
        if path:
            return path
    return None


def unavailable_reason():
    if os.environ.get("SKIP_BROWSER_TESTS"):
        return "SKIP_BROWSER_TESTS is set"
    if not find_browser():
        return "no Chromium/Chrome found on the PATH"
    node = shutil.which("node")
    if not node:
        return "Node is not installed"
    version = subprocess.run(
        [node, "--version"], capture_output=True, text=True, check=False
    ).stdout
    match = re.match(r"v(\d+)", version)
    if not match or int(match.group(1)) < 22:
        return (
            f"Node 22+ is required for its built-in WebSocket (found {version.strip()})"
        )
    try:
        urllib.request.urlopen(CHART_JS_URL, timeout=5).close()
    except OSError:
        return "the Chart.js CDN is unreachable (the pages load it from there)"
    return None


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_until(check, seconds, what):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if check():
                return
        except OSError:
            pass
        time.sleep(0.1)
    raise AssertionError(f"timed out waiting for {what}")


def profile(name, roaster_id, temps, first_crack, development):
    return {
        "name": name,
        "roaster_id": roaster_id,
        "temps": temps,
        "target_first_crack": first_crack,
        "target_development_time": development,
        "favorite": False,
        "owner": OWNER,
    }


def record(profile_id, roaster_id, unit, temps, **overrides):
    saved = {
        "date": "09/07/2026",
        "bean_name": "Fixture bean",
        "green_weight": 200.0,
        "finished_weight": 170.0,
        "total_roast_time": 720,
        "time_of_first_crack": 540,
        "roast_profile_id": profile_id,
        "roaster_id": roaster_id,
        "temp_unit": unit,
        "target_temps": temps,
        "actual_temps": temps,
        "owner": OWNER,
    }
    saved.update(overrides)
    return saved


SR800_TEMPS = [320, 365, 400, 430, 445, 455, 460] + [None] * 5
KAFFELOGIC_TEMPS = [150, 175, 190, 200, 205] + [None] * 7
GENE_CAFE_TEMPS = [300, 350, 400, 430, 450] + [None] * 20
HOTTOP_TEMPS = [250, 300, 340, 370, 385] + [None] * 22
QUEST_TEMPS = [150, 170, 185, 195, 205] + [None] * 19
PROFILES = {
    "p-hottop": profile("Hottop", "hottop-kn-8828b-2k", HOTTOP_TEMPS, 750, 120),
    "p-quest": profile("Quest", "quest-m3", QUEST_TEMPS, 720, 100),
    "p-sr540": profile("SR540", "fresh-roast-sr540", SR800_TEMPS, 375, 75),
    "p-sr800": profile("SR800 medium", "fresh-roast-sr800", SR800_TEMPS, 375, 75),
    "p-kaffelogic": profile(
        "Kaffelogic", "kaffelogic-nano-7", KAFFELOGIC_TEMPS, 400, 100
    ),
    "p-genecafe": profile(
        "Gene Cafe", "gene-cafe-cbr-101", GENE_CAFE_TEMPS, None, None
    ),
    "p-whirley": profile(
        "Whirley-Pop", "whirley-pop-stovetop-popcorn-popper", [None] * 12, 360, 90
    ),
}
RECORDS = {
    "r-sr800": record(
        "p-sr800",
        "fresh-roast-sr800",
        "F",
        SR800_TEMPS,
        start_condition="warm",
        ambient_temp=68.0,
    ),
    "r-kaffelogic": record(
        "p-kaffelogic",
        "kaffelogic-nano-7",
        "C",
        KAFFELOGIC_TEMPS,
        start_condition="cold",
        ambient_temp=21.5,
    ),
    "r-genecafe": record("p-genecafe", "gene-cafe-cbr-101", "F", GENE_CAFE_TEMPS),
    "r-whirley": record(
        "p-whirley",
        "whirley-pop-stovetop-popcorn-popper",
        None,
        [None] * 12,
        start_condition="preheated",
    ),
}


class TestBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reason = unavailable_reason()
        if reason:
            raise unittest.SkipTest(reason)

        tmp = Path(tempfile.mkdtemp(prefix="crackle-browser-"))
        cls.addClassCleanup(shutil.rmtree, tmp, ignore_errors=True)
        data_dir = tmp / "data"
        data_dir.mkdir()
        (data_dir / "roast_profiles.json").write_text(json.dumps(PROFILES))
        (data_dir / "roast_records.json").write_text(json.dumps(RECORDS))
        (data_dir / "users.json").write_text("{}")

        app_port, debug_port = free_port(), free_port()
        server_log = tmp / "server.log"
        with open(server_log, "w") as log:  # the child keeps its own handle
            server = subprocess.Popen(
                [sys.executable, str(HERE / "serve.py"), str(app_port), str(data_dir)],
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        cls.addClassCleanup(cls.stop, server)
        base_url = f"http://127.0.0.1:{app_port}"
        try:
            wait_until(
                lambda: urllib.request.urlopen(base_url + "/about"),
                20,
                "the app to start",
            )
        except AssertionError as error:
            raise AssertionError(
                f"{error}\n--- server log ---\n{server_log.read_text()}"
            )

        chromium = subprocess.Popen(
            [
                find_browser(),
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                f"--remote-debugging-port={debug_port}",
                f"--user-data-dir={tmp / 'profile'}",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls.addClassCleanup(cls.stop, chromium)
        wait_until(
            lambda: urllib.request.urlopen(f"http://127.0.0.1:{debug_port}/json"),
            20,
            "Chromium's debugging port",
        )

        driver = subprocess.run(
            ["node", str(HERE / "driver.mjs"), str(debug_port), base_url],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,  # a non-zero exit is reported below, with the driver's output
        )
        if driver.returncode != 0:
            raise AssertionError(f"driver failed:\n{driver.stderr}\n{driver.stdout}")
        cls.results = json.loads(driver.stdout)

    @staticmethod
    def stop(process):
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    def scenario(self, name):
        data = self.results[name]
        self.assertNotIn("error", data, data.get("error"))
        self.assertEqual(data["problems"], [], f"console problems in {name}")
        return data

    # ---- Add Roast ----

    def test_sr800_live_chart_is_drawn_from_the_roasters_own_data(self):
        page = self.scenario("addRoastSr800")
        self.assertTrue(page["chartLibLoaded"])
        self.assertFalse(page["graphHidden"])
        self.assertTrue(page["layoutHeightSet"])
        chart = page["chart"]
        self.assertEqual(chart["datasets"], 4)
        self.assertEqual(chart["curvePoints"], 121)
        self.assertEqual(chart["xMax"], 12)
        self.assertEqual(chart["yTitle"], "Temperature (°F)")
        self.assertEqual(chart["y1Title"], "Rate of rise (°F/min)")
        # The opening comes from the SR800's chart anchors (145 start, 270 at 30 s).
        expected = [
            (0, 145),
            (0.1, 176.5142857),
            (0.2, 205.5428571),
            (0.3, 231.3142857),
        ]
        for point, (x, y) in zip(chart["curveStart"], expected):
            self.assertAlmostEqual(point["x"], x, places=6)
            self.assertAlmostEqual(point["y"], y, places=5)
        self.assertEqual(page["targetReadout"], "145°F")
        self.assertRegex(page["rorReadoutInitial"], r"^-?\d+°F/min$")

    def test_sr800_page_text_and_units(self):
        page = self.scenario("addRoastSr800")
        self.assertEqual(page["actualTempInputs"], 12)
        self.assertIn("Actual (°F)", page["tableHeaders"])
        self.assertIn("Target (°F)", page["tableHeaders"])
        self.assertEqual(
            page["targetReference"],
            "Target first crack: 6:15 · Target development time: 1:15",
        )
        self.assertTrue(any("Allowed 113–227 g" in hint for hint in page["hints"]))
        self.assertFalse(page["hasCelsius"])
        # The owner confirmed the SR800's 30-minute rule, so it is shown as a reminder.
        self.assertEqual(
            page["notes"],
            ["Reminder: this roaster needs at least 30 minutes between roasts."],
        )

    def test_add_roast_offers_start_condition_and_ambient_in_the_roasters_unit(self):
        for name, ambient in (
            ("addRoastSr800", "Ambient temperature, °F (optional)"),
            ("addRoastCelsius", "Ambient temperature, °C (optional)"),
            ("addRoastNoReadout", None),
        ):
            with self.subTest(page=name):
                page = self.scenario(name)
                self.assertEqual(
                    page["startConditionOptions"],
                    ["— not recorded —", "Cold start", "Warm start", "Preheated"],
                )
                self.assertEqual(page["ambientLabel"], ambient)

    def test_sr800_timer_first_crack_and_pull_countdown(self):
        page = self.scenario("addRoastSr800")
        self.assertEqual(page["dateFormatted"], "09/19/2026")
        running = page["running"]
        self.assertEqual(running["button"], "Stop")
        self.assertRegex(running["clock"], CLOCK)
        self.assertRegex(running["targetReadout"], r"^\d+°F$")
        self.assertRegex(running["rorReadout"], r"^-?\d+°F/min$")
        self.assertRegex(page["firstCrackValue"], CLOCK)
        # Target development time 1:15 after a first crack a second or so in.
        self.assertRegex(page["pullCountdown"], r"^Pull in [01]:\d\d$")
        self.assertEqual(page["afterStop"], "Start")
        self.assertEqual(page["afterReset"], "0:00")

    def test_celsius_roaster_uses_celsius_everywhere_and_starts_at_its_first_target(
        self,
    ):
        page = self.scenario("addRoastCelsius")
        chart = page["chart"]
        self.assertEqual(chart["yTitle"], "Temperature (°C)")
        self.assertEqual(chart["y1Title"], "Rate of rise (°C/min)")
        self.assertEqual(chart["xMax"], 12)
        # No known opening for this roaster: the curve begins at its first target (minute 1),
        # not with an invented ramp or a flat lead-in, and then heads for the next target.
        start = chart["curveStart"]
        self.assertAlmostEqual(start[0]["x"], 1, places=6)
        self.assertAlmostEqual(start[0]["y"], 150, places=3)
        self.assertGreater(start[3]["y"], 150)
        # The rate-of-rise line starts at the curve's real slope, not half of it.
        ror = chart["rorStart"]
        self.assertAlmostEqual(ror[0]["x"], 1, places=6)
        self.assertGreater(ror[0]["y"], 0.9 * ror[1]["y"])
        self.assertEqual(page["targetReadout"], "150°C")
        # There is no slope to report before the curve begins.
        self.assertEqual(page["rorReadoutInitial"], "\u2013")
        self.assertIn("Actual (°C)", page["tableHeaders"])
        self.assertRegex(page["running"]["targetReadout"], r"^\d+°C$")
        # A couple of seconds in, this roaster's curve (which begins at minute 1) has no slope yet.
        self.assertEqual(page["running"]["rorReadout"], "\u2013")
        self.assertTrue(page["hasCelsius"])
        self.assertFalse(page["hasFahrenheit"])
        self.assertRegex(page["pullCountdown"], r"^Pull in \d:\d\d$")

    def test_a_25_row_profile_gets_25_rows_and_a_25_minute_axis(self):
        page = self.scenario("addRoastGeneCafe")
        self.assertEqual(page["actualTempInputs"], 25)
        self.assertEqual(page["chart"]["xMax"], 25)
        # One point per 0.1 minute from the first target (minute 1) to minute 25; floating-point
        # accumulation may stop one short of 241.
        self.assertIn(page["chart"]["curvePoints"], (240, 241))
        self.assertEqual(page["chart"]["yTitle"], "Temperature (°F)")
        self.assertTrue(any("Up to 25:00" in hint for hint in page["hints"]))

    def test_a_preheat_and_charge_roaster_starts_its_curve_at_its_stated_charge_temperature(
        self,
    ):
        page = self.scenario("addRoastPreheatCharge")
        chart = page["chart"]
        # Hottop: beans go in at the 167 F preheat beep; the curve heads from there to the first target.
        self.assertAlmostEqual(chart["curveStart"][0]["x"], 0, places=6)
        self.assertAlmostEqual(chart["curveStart"][0]["y"], 167, places=6)
        self.assertGreater(chart["curveStart"][3]["y"], 167)
        self.assertEqual(page["targetReadout"], "167°F")
        self.assertEqual(chart["xMax"], 27)
        self.assertEqual(chart["yTitle"], "Temperature (°F)")

    def test_the_pull_countdown_allows_for_the_roasters_coast_time(self):
        page = self.scenario("addRoastCoast")
        # Target development 1:40 minus 20 s of coast: about 1:20 left just after first crack.
        self.assertRegex(page["pullCountdown"], r"^Pull in 1:[12]\d$")
        self.assertTrue(any("allows 20 s" in note for note in page["notes"]))
        # The same countdown on a roaster with no coast time (Celsius fixture: 1:40 -> about 1:39).
        self.assertRegex(
            self.scenario("addRoastCelsius")["pullCountdown"], r"^Pull in 1:[34]\d$"
        )

    def test_a_stated_gap_between_roasts_is_shown_as_a_reminder(self):
        page = self.scenario("addRoastSr540")
        self.assertEqual(
            page["notes"],
            ["Reminder: this roaster needs at least 30 minutes between roasts."],
        )
        # A stated gap of zero (back-to-back is fine) shows nothing.
        self.assertFalse(
            any("Reminder" in note for note in self.scenario("addRoastCoast")["notes"])
        )

    def test_roaster_without_a_readout_hides_the_chart_but_keeps_the_timer(self):
        page = self.scenario("addRoastNoReadout")
        self.assertTrue(page["graphHidden"])
        self.assertTrue(page["targetReadoutHidden"])
        self.assertEqual(page["actualTempInputs"], 0)
        self.assertIsNone(page["chart"])
        self.assertFalse(page["hasFahrenheit"] or page["hasCelsius"])
        self.assertRegex(page["running"]["clock"], CLOCK)
        self.assertRegex(page["firstCrackValue"], CLOCK)
        self.assertRegex(page["pullCountdown"], r"^Pull in \d:\d\d$")
        self.assertEqual(page["afterReset"], "0:00")

    # ---- Profile pages ----

    def test_wizard_output_for_the_sr800(self):
        wizard = self.scenario("wizard")
        self.assertTrue(wizard["panelHiddenAtStart"])
        self.assertTrue(wizard["panelShownAfterToggle"])
        self.assertEqual(
            wizard["defaultInputs"],
            {
                "temps": [
                    "315",
                    "343",
                    "366",
                    "383",
                    "394",
                    "400",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ],
                "firstCrack": "6:15",
                "developmentTime": "1:11",
            },
        )
        self.assertEqual(
            wizard["otherInputs"],
            {
                "temps": [
                    "315",
                    "344",
                    "367",
                    "386",
                    "401",
                    "410",
                    "415",
                    "",
                    "",
                    "",
                    "",
                    "",
                ],
                "firstCrack": "7:05",
                "developmentTime": "1:46",
            },
        )

    def test_an_sr_model_without_calibration_gets_the_same_curve_and_the_notice(self):
        wizard = self.scenario("wizardEstimatedCurve")
        self.assertTrue(wizard["notice"])
        self.assertFalse(wizard["noCurveMessage"])
        self.assertEqual(wizard["fcTempInput"], "400")
        self.assertEqual(
            wizard["washed"],
            {
                "temps": [
                    "315",
                    "343",
                    "366",
                    "383",
                    "394",
                    "400",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ],
                "firstCrack": "6:15",
                "developmentTime": "1:11",
            },
        )
        # Natural process adds the SR family's 20 s to first crack.
        self.assertEqual(wizard["natural"]["firstCrack"], "6:35")
        self.assertEqual(wizard["natural"]["developmentTime"], "1:15")

    def test_a_roaster_without_start_temperatures_gets_times_only(self):
        wizard = self.scenario("wizardTimesOnly")
        self.assertTrue(wizard["notice"])
        self.assertTrue(wizard["noCurveMessage"])
        self.assertIsNone(wizard["fcTempInput"])
        # Kaffelogic's worked example: first crack at 7:30; Full City DTR 21% -> 2:00.
        self.assertEqual(wizard["washed"]["firstCrack"], "7:30")
        self.assertEqual(wizard["washed"]["developmentTime"], "2:00")
        # The temperature grid is left alone (all 12 rows still blank).
        self.assertEqual(wizard["washed"]["temps"], [""] * 12)
        # No natural-process adjustment is known for it, so process changes nothing.
        self.assertEqual(wizard["natural"]["firstCrack"], "7:30")

    def test_the_wizard_follows_a_25_row_roasters_own_data(self):
        wizard = self.scenario("wizardLongGrid")
        self.assertEqual(wizard["tempInputs"], 25)
        self.assertEqual(wizard["washed"]["temps"], [""] * 25)
        self.assertEqual(wizard["washed"]["firstCrack"], "15:00")
        self.assertEqual(wizard["washed"]["developmentTime"], "3:59")
        # Gene Cafe's natural adjustment is negative (dry-process coffee roasts faster).
        self.assertEqual(wizard["natural"]["firstCrack"], "14:30")
        self.assertEqual(wizard["natural"]["developmentTime"], "3:51")

    def test_a_roaster_without_a_readout_has_no_wizard(self):
        self.assertFalse(self.scenario("wizardNone")["toggle"])

    def test_edit_page_shows_the_locked_roaster_and_no_wizard(self):
        page = self.scenario("editProfile")
        self.assertFalse(page["hasWizard"])
        self.assertFalse(page["hasSelect"])
        self.assertFalse(page["hasRoasterInput"])
        self.assertTrue(page["showsRoaster"])
        self.assertEqual(page["tempInputs"], 12)

    def test_choosing_a_roaster_first_then_the_form_for_it(self):
        page = self.scenario("chooser")
        self.assertEqual(page["optionCount"], len(load_roasters()) + 1)
        self.assertIn("Select a roaster", page["firstOption"])
        self.assertFalse(page["formShownAtStart"])
        self.assertEqual(page["search"], "?roaster=gene-cafe-cbr-101")
        self.assertTrue(page["formShownAfter"])
        self.assertEqual(page["roasterInput"], "gene-cafe-cbr-101")
        self.assertTrue(page["showsRoaster"])
        self.assertEqual(page["tempInputs"], 25)

    # ---- Roast list ----

    def test_the_roast_list_has_a_roaster_column_that_sorts_and_searches_correctly(
        self,
    ):
        page = self.scenario("roastsList")
        self.assertEqual(
            page["headers"],
            [
                "Date",
                "Bean Name",
                "Roast Profile",
                "Roaster",
                "Green (g)",
                "Finished (g)",
                "Roast Time",
                "1st Crack",
                "Weight Loss (%)",
                "Dev Time",
                "Classification",
            ],
        )
        names = sorted(page["unsorted"])
        self.assertEqual(len(names), len(RECORDS))
        self.assertIn("Fresh Roast SR800", names)
        self.assertEqual(page["ascending"], names)
        self.assertEqual(page["descending"], names[::-1])
        # Search still matches the profile column and hides the rest.
        self.assertEqual(page["searched"], ["Kaffelogic Nano 7"])

    # ---- Roast detail ----

    def test_roast_detail_charts_use_the_records_unit_and_row_count(self):
        for name, unit, rows in (
            ("detailSr800", "°F", 12),
            ("detailCelsius", "°C", 12),
            ("detailGeneCafe", "°F", 25),
        ):
            with self.subTest(page=name):
                page = self.scenario(name)
                charts = page["charts"]
                self.assertEqual(charts["labelCount"], rows)
                self.assertEqual(page["tableRows"], rows)
                self.assertEqual(
                    charts["datasetLabels"], [f"Target ({unit})", f"Actual ({unit})"]
                )
                self.assertEqual(charts["tempYTitle"], f"Temperature ({unit})")
                self.assertEqual(charts["rorYTitle"], f"Rate of rise ({unit}/min)")
                self.assertTrue(page["showsRoaster"])
                self.assertEqual(page["hasCelsius"], unit == "°C")
                self.assertEqual(page["hasFahrenheit"], unit == "°F")

    def test_roast_detail_shows_the_start_condition_and_ambient_in_the_records_unit(
        self,
    ):
        for name, conditions in (
            ("detailSr800", "Warm start · Ambient 68°F"),
            ("detailCelsius", "Cold start · Ambient 21.5°C"),
            ("detailNoReadout", "Preheated"),
            ("detailGeneCafe", None),
        ):
            with self.subTest(page=name):
                self.assertEqual(self.scenario(name)["conditions"], conditions)

    def test_logging_a_roast_through_the_form_saves_the_start_condition_and_ambient(
        self,
    ):
        page = self.scenario("submitRoast")
        # 60 is a sensible room temperature in Fahrenheit but not in this Celsius roaster:
        # the form comes back with the message and everything typed, saving nothing.
        rejected = page["rejected"]
        self.assertRegex(rejected["path"], r"^/roasts/new/")
        self.assertIn("between -18 and 49", rejected["error"])
        self.assertEqual(rejected["selectedCondition"], "cold")
        self.assertEqual(rejected["ambientValue"], "60")
        self.assertEqual(rejected["beanName"], "Browser Bean")
        # Corrected, it saves and lands on the new roast's page.
        self.assertRegex(page["savedPath"], r"^/roasts/[^/]+$")
        self.assertIn("Browser Bean", page["heading"])
        self.assertEqual(page["conditions"], "Cold start · Ambient 21.5°C")

    def test_roast_detail_for_a_roaster_without_a_readout_has_no_temperature_charts(
        self,
    ):
        page = self.scenario("detailNoReadout")
        self.assertFalse(page["hasTempChart"])
        self.assertIsNone(page["charts"])
        self.assertIsNone(page["tableRows"])
        self.assertTrue(page["showsRoaster"])

    # ---- Phone-sized screens ----
    PHONE_PAGES = (
        "phoneAddRoast",
        "phoneAddRoastLong",
        "phoneAddRoastNoReadout",
        "phoneRoasts",
        "phoneDetail",
        "phonePicker",
        "phoneProfiles",
        "phoneChooser",
        "phoneProfileForm",
        "phoneAbout",
    )

    def test_every_page_lays_out_at_phone_width(self):
        for name in self.PHONE_PAGES:
            with self.subTest(page=name):
                page = self.scenario(name)
                self.assertEqual(
                    page["viewportMeta"], "width=device-width, initial-scale=1"
                )
                # Without the viewport tag a phone lays a page out at 980 px and shrinks it.
                self.assertEqual(page["layoutWidth"], 390)
                self.assertFalse(page["pageScrollsSideways"])

    def test_phone_fields_and_buttons_are_big_enough_to_type_in_and_tap(self):
        for name in self.PHONE_PAGES:
            with self.subTest(page=name):
                page = self.scenario(name)
                # Under 16 px iOS zooms the page when a field is focused.
                self.assertEqual(page["fieldsUnder16px"], [])
                self.assertEqual(page["controlsUnder44px"], [])

    def test_on_a_phone_the_timer_and_first_crack_button_come_before_the_form(self):
        for name in ("phoneAddRoast", "phoneAddRoastLong", "phoneAddRoastNoReadout"):
            with self.subTest(page=name):
                page = self.scenario(name)
                self.assertLess(page["liveTop"], page["formTop"])
                self.assertLessEqual(
                    page["firstCrackButton"]["bottom"], page["formTop"]
                )
                self.assertLessEqual(page["startButton"]["bottom"], page["formTop"])

    def test_the_live_chart_is_4_to_3_on_a_phone_and_2_to_1_on_a_desktop(self):
        for name in ("phoneAddRoast", "phoneAddRoastLong"):
            with self.subTest(page=name):
                self.assertAlmostEqual(
                    self.scenario(name)["chartShape"], 0.75, delta=0.02
                )
        self.assertAlmostEqual(
            self.scenario("addRoastSr800")["chartShape"], 0.5, delta=0.02
        )

    def test_the_date_and_calendar_button_fit_inside_the_card_on_a_phone(self):
        page = self.scenario("phoneAddRoast")
        self.assertLessEqual(page["dateField"]["right"], page["card"]["right"])
        self.assertGreaterEqual(page["datePicker"]["width"], 100)

    def test_on_a_tablet_the_date_row_fits_inside_the_narrow_form_column(self):
        page = self.scenario("tabletAddRoast")
        self.assertEqual(page["layoutWidth"], 768)
        self.assertFalse(page["pageScrollsSideways"])
        # The two-column layout is kept above the phone breakpoint, and the calendar
        # button must not be cut off by the form column's edge.
        self.assertGreater(page["formTop"], 0)
        self.assertLessEqual(page["dateField"]["right"], page["formColumn"]["right"])
        self.assertLessEqual(
            page["datePicker"]["right"], page["dateField"]["right"] + 0.5
        )

    def test_the_detail_charts_are_4_to_3_on_a_phone(self):
        for shape in self.scenario("phoneDetail")["detailChartShapes"]:
            self.assertAlmostEqual(shape, 0.75, delta=0.02)

    def test_the_wide_roast_table_scrolls_sideways_with_a_hint_only_on_a_phone(self):
        phone = self.scenario("phoneRoasts")
        self.assertEqual(phone["scrollHint"], "block")
        self.assertTrue(phone["tableScrolls"])
        self.assertEqual(self.scenario("roastsList")["scrollHint"], "none")


if __name__ == "__main__":
    unittest.main()
