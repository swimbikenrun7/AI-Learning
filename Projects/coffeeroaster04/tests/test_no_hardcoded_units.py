"""Guard: no template, script, or module may hard-code a temperature unit.

Every temperature is shown in its roaster's own unit, taken from roasters.TEMP_UNITS. A
literal degree-and-unit (a Fahrenheit or Celsius label written into a page or script)
would show the wrong unit for the other kind of roaster, so the only place the symbols
may appear is the units table itself.
"""

import pathlib
import re
import unittest

from roasters import TEMP_UNITS

ROOT = pathlib.Path(__file__).resolve().parent.parent
UNIT_LITERAL = re.compile(r"(°|&deg;|&#176;|\\u00b0)\s*[FC]\b", re.IGNORECASE)


def checked_files():
    for folder, suffixes in (("templates", {".html"}), ("static", {".js", ".css"})):
        for path in sorted((ROOT / folder).rglob("*")):
            if path.suffix in suffixes:
                yield path
    for name in ("app.py", "validators.py", "calculations.py"):
        yield ROOT / name


class TestNoHardcodedUnits(unittest.TestCase):
    def test_no_page_script_or_module_writes_a_unit_literal(self):
        found = []
        for path in checked_files():
            for number, line in enumerate(path.read_text().splitlines(), start=1):
                if UNIT_LITERAL.search(line):
                    found.append(
                        f"{path.relative_to(ROOT)}:{number}: {line.strip()[:80]}"
                    )
        self.assertEqual(found, [], "hard-coded unit literals:\n" + "\n".join(found))

    def test_the_units_table_is_the_one_place_symbols_live(self):
        self.assertEqual(set(TEMP_UNITS), {"F", "C"})
        for unit, row in TEMP_UNITS.items():
            self.assertTrue(row["symbol"].endswith(unit))
            self.assertEqual(row["ror"], row["symbol"] + "/min")

    def test_the_guard_pattern_catches_what_it_should(self):
        for bad in (
            "Target (°F)",
            "Actual (&deg;C)",
            "° F",
            "text: 'Temperature (°C)'",
            "\\u00b0F",
        ):
            with self.subTest(bad=bad):
                self.assertTrue(UNIT_LITERAL.search(bad))
        for fine in (
            "Full City",
            "{{ units.symbol }}",
            "180 degrees",
            "°",
            "Cool",
            "F1 button",
        ):
            with self.subTest(fine=fine):
                self.assertFalse(UNIT_LITERAL.search(fine))


if __name__ == "__main__":
    unittest.main()
