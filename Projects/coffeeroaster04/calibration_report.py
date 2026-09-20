"""Read-only calibration report: how logged roasts compare with each roaster's stored values.

usage: python calibration_report.py [--records PATH]

Reads the roast records (default: data/roast_records.json) and data/roasters.json and prints,
for each roaster that has logged roasts, the time to first crack, weight loss, temperature at
first crack, and development ratio by roast level, next to the values stored for that roaster.
Nothing is written and no app code runs, so it is safe to point at a copy of the live data.
Records from every owner in the file are combined; no names appear in the report.

Changing a roaster's values, or flipping its `calibrated` flag, stays a manual edit of
data/roasters.json.
"""

import argparse
import statistics
import sys
from pathlib import Path

import calculations as calc
import data_persistence
from roasters import PROFILE_STYLES, TEMP_UNITS, profile_style, wizard_for_style

# When to suggest that a roaster's stored values could be tuned from its own roasts. These are
# starting points, not domain rules: the numbers are printed so the call stays with the owner.
MIN_ROASTS = 5
MAX_FIRST_CRACK_SPREAD_S = 60


def format_mm_ss(total_seconds):
    minutes, seconds = divmod(round(total_seconds), 60)
    return f"{minutes}:{seconds:02d}"


def format_signed_mm_ss(difference_seconds):
    sign = "-" if round(difference_seconds) < 0 else "+"
    return sign + format_mm_ss(abs(difference_seconds))


def temperature_at_first_crack(actual_temps, first_crack_seconds):
    """Temperature at first crack, read from the once-a-minute actual temperatures.

    Row k of the list is the reading at minute k+1, so first crack falls between two rows;
    the answer is a straight line between them. None if either reading is missing or first
    crack came before the first reading.
    """
    minute, seconds = divmod(first_crack_seconds, 60)
    if minute < 1 or minute > len(actual_temps):
        return None
    before = actual_temps[minute - 1]
    if seconds == 0:
        return before
    if minute == len(actual_temps):
        return None
    after = actual_temps[minute]
    if before is None or after is None:
        return None
    return before + (after - before) * seconds / 60


def summarize(records, values):
    """The numbers the report compares, gathered from one roaster's saved records.

    Saved records were validated against their roaster's limits when they were saved, so the
    original calculation guards are opened here, the same as when a roast is displayed.
    """
    summary = {
        "first_crack": [],
        "total_time": [],
        "weight_loss": [],
        "temp_at_first_crack": [],
        "dtr_by_level": {},
    }
    for record in records:
        first_crack = record["time_of_first_crack"]
        total = record["total_roast_time"]
        weight_loss = calc.calculate_weight_loss(
            record["green_weight"],
            record["finished_weight"],
            min_g=0,
            max_g=float("inf"),
        )
        development = calc.calculate_development_time(total, first_crack, 0)
        level = calc.classify_roast(weight_loss)
        summary["first_crack"].append(first_crack)
        summary["total_time"].append(total)
        summary["weight_loss"].append(weight_loss)
        summary["dtr_by_level"].setdefault(level, []).append(
            calc.calculate_dtr(total, development)
        )
        # A reading in another unit than the roaster's would compare nonsense with its stored value.
        if record.get("temp_unit") == values.get("temp_unit"):
            temp = temperature_at_first_crack(record["actual_temps"], first_crack)
            if temp is not None:
                summary["temp_at_first_crack"].append(temp)
    return summary


def median_and_range(numbers, fmt):
    return (
        f"median {fmt(statistics.median(numbers))}"
        f"   range {fmt(min(numbers))}-{fmt(max(numbers))}"
    )


def record_style(record):
    return profile_style({"style": record.get("profile_style")})


def roaster_section(roaster_id, roaster, records, style="drip"):
    values = roaster["values"] if roaster else {}
    name = roaster["name"] if roaster else (roaster_id or "No roaster recorded")
    if style != "drip":
        name += f" ({PROFILE_STYLES[style]})"
    summary = summarize(records, values)
    # Each style is compared with its own stored values, and only drip is ever calibrated.
    wizard = wizard_for_style(values.get("wizard"), style) or {}
    calibrated = bool(values.get("calibrated")) and style == "drip"
    unit = TEMP_UNITS.get(values.get("temp_unit"), {}).get("symbol", "")
    first_crack = summary["first_crack"]
    plural = "roast" if len(records) == 1 else "roasts"
    status = ""
    if roaster:
        status = " — calibrated" if calibrated else " — not calibrated"
    lines = [f"{name}: {len(records)} {plural}{status}"]

    def line(label, text):
        lines.append(f"  {label:<28}{text}")

    text = median_and_range(first_crack, format_mm_ss)
    stored = (wizard.get("time_to_first_crack_s") or {}).get("medium")
    if stored is not None:
        difference = statistics.median(first_crack) - stored
        text += (
            f"   stored {format_mm_ss(stored)}"
            f" (medium density, washed)   difference {format_signed_mm_ss(difference)}"
        )
    line("Time to first crack", text)
    line("Total roast time", median_and_range(summary["total_time"], format_mm_ss))
    line(
        "Weight loss",
        median_and_range(summary["weight_loss"], lambda n: f"{n:.1f}%"),
    )

    temps = summary["temp_at_first_crack"]
    if temps:
        text = median_and_range(temps, lambda n: f"{n:.0f}{unit}")
        text += f"   ({len(temps)} of {len(records)} with readings)"
        stored = wizard.get("default_first_crack_temp")
        if stored is not None:
            difference = statistics.median(temps) - stored
            text += f"   stored {stored:g}{unit}   difference {difference:+.0f}{unit}"
        line("Temperature at first crack", text)

    lines.append(
        "  Development ratio by roast level (roast level comes from weight loss):"
    )
    for level, ratios in summary["dtr_by_level"].items():
        text = f"n={len(ratios)}   observed {statistics.mean(ratios):.1f}%"
        stored = (wizard.get("dtr_by_level") or {}).get(level)
        if stored is not None:
            difference = statistics.mean(ratios) - stored * 100
            text += f"   stored {stored * 100:.1f}%   difference {difference:+.1f}"
        lines.append(f"    {level:<16}{text}")

    if roaster and calibrated:
        lines.append("  Already calibrated: the differences above show any drift.")
    elif roaster:
        spread = max(first_crack) - min(first_crack)
        if len(records) < MIN_ROASTS:
            verdict = f"not enough roasts yet ({len(records)} of {MIN_ROASTS})"
        elif spread > MAX_FIRST_CRACK_SPREAD_S:
            verdict = (
                f"first-crack times are too spread out ({format_mm_ss(spread)} apart; "
                f"within {MAX_FIRST_CRACK_SPREAD_S} s wanted)"
            )
        else:
            verdict = "yes"
        lines.append(f"  Enough consistent data to consider calibrating? {verdict}")
    return lines


def build_report(records, roasters, source):
    # One group per roaster and style: espresso roasts are never averaged into drip ones.
    by_roaster = {}
    for record in records.values():
        key = (record.get("roaster_id"), record_style(record))
        by_roaster.setdefault(key, []).append(record)
    if not by_roaster:
        return f"No roasts logged in {source}."

    def order(key):
        roaster_id, style = key
        roaster = roasters.get(roaster_id)
        return (
            -len(by_roaster[key]),
            roaster is None,
            roaster["name"] if roaster else "",
            style,
        )

    lines = [f"Calibration report: {len(records)} roasts from {source}", ""]
    for key in sorted(by_roaster, key=order):
        roaster_id, style = key
        lines += roaster_section(
            roaster_id, roasters.get(roaster_id), by_roaster[key], style
        )
        lines.append("")
    lines.append(
        "To tune a roaster, edit its values in data/roasters.json and set `calibrated` "
        "yourself; this report changes nothing."
    )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--records",
        type=Path,
        default=data_persistence.ROAST_RECORDS_PATH,
        help="roast records file to read (default: data/roast_records.json)",
    )
    args = parser.parse_args(argv)
    if not args.records.exists():
        print(f"Error: no roast records file at {args.records}.", file=sys.stderr)
        return 1
    # The loaders stop with a message on a corrupted file rather than reporting on partial data.
    # The records loader reads its path from the module, so point it at the chosen file and back.
    default_path = data_persistence.ROAST_RECORDS_PATH
    data_persistence.ROAST_RECORDS_PATH = args.records
    try:
        records = data_persistence.load_roast_records()
    finally:
        data_persistence.ROAST_RECORDS_PATH = default_path
    roasters = data_persistence.load_roasters()
    print(build_report(records, roasters, args.records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
