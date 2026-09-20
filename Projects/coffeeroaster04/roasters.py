"""Per-roaster settings: which limits, units, and grid length apply to a profile.

Pure functions over the roasters dict loaded from data/roasters.json; no Flask, no I/O.
"""

# What a profile is for. "drip" is what every profile was before styles existed (and the
# default); "espresso" develops longer. A profile's style, like its roaster, is chosen when it
# is created and never changes.
PROFILE_STYLES = {"drip": "Drip", "espresso": "Espresso"}
DEFAULT_PROFILE_STYLE = "drip"


def profile_style(profile):
    """A saved profile's style; one saved before styles existed (or unknown) is drip."""
    style = (profile or {}).get("style")
    return style if style in PROFILE_STYLES else DEFAULT_PROFILE_STYLE


def wizard_for_style(wizard, style):
    """The wizard values to use for a profile style, or None if there are none.

    Drip is the roaster's base `wizard` block. Espresso replaces the values that depend on
    the style (first-crack time, natural adjustment, development-time ratios) with the
    block's `espresso` values and keeps the roaster's start and first-crack temperatures,
    which belong to the machine, not the style. A roaster with no espresso values has no
    espresso wizard.
    """
    if not wizard:
        return None
    base = {key: value for key, value in wizard.items() if key != "espresso"}
    if style == "espresso":
        override = wizard.get("espresso")
        return {**base, **override} if override else None
    return base


# What applied before roasters carried their own data. Used for a profile with no roaster
# (or an unknown roaster id), and per field where a roaster's value is null.
LEGACY_SETTINGS = {
    "green_weight_min_g": 100,
    "green_weight_max_g": 300,
    "green_weight_recommended_g": None,
    "finished_weight_min_g": 100,
    "roast_time_min_s": 240,
    "roast_time_max_s": 1199,  # legacy rule: total roast time < 20:00
    "first_crack_min_s": 240,
    "profile_grid_minutes": 12,
    "calibrated": False,
    "wizard": None,
    "has_temp_readout": True,
    "temp_unit": "F",
    "temp_source": "unspecified",
    "temp_min": 60,
    "temp_max": 500,
    # Live-chart opening anchors (start temp; minutes and temp of the first inflection).
    "chart_start_temp": 145,
    "chart_inflection_min": 0.5,
    "chart_inflection_temp": 270,
    "start_model": "ramp",
    "preheat_temp": None,
    "charge_temp": None,
    "cooling_coast_seconds": None,
    "min_gap_between_roasts_min": None,
    "min_gap_stated": False,  # true only if a source states the gap (not inferred)
}

# Every temperature for a roaster is stored and shown in that roaster's own unit and is
# never converted; the only unit-specific text lives here, so no template or script
# carries a literal unit.
TEMP_UNITS = {
    # ambient_min/ambient_max: a plausible room or outdoor air temperature to record.
    "F": {"symbol": "°F", "ror": "°F/min", "ambient_min": 0, "ambient_max": 120},
    "C": {"symbol": "°C", "ror": "°C/min", "ambient_min": -18, "ambient_max": 49},
}

_FIELDS_WITH_FALLBACK = [
    "green_weight_min_g",
    "green_weight_max_g",
    "green_weight_recommended_g",
    "roast_time_min_s",
    "first_crack_min_s",
    "profile_grid_minutes",
]
_CHART_FIELDS = ["chart_start_temp", "chart_inflection_min", "chart_inflection_temp"]


def settings_for(roasters, roaster_id, rows=None):
    """Resolve the settings that apply to a roaster id.

    `rows` is the number of rows an existing profile actually has; it sets the maximum
    roast time (a roast can never run past the rows that describe it). Without it, the
    roaster's own grid length is used.
    """
    settings = dict(LEGACY_SETTINGS)
    settings["roaster_id"] = None
    settings["roaster_name"] = None
    roaster = roasters.get(roaster_id) if roaster_id else None

    if roaster is not None:
        values = roaster.get("values") or {}
        settings["roaster_id"] = roaster_id
        settings["roaster_name"] = roaster.get("name")
        settings["calibrated"] = bool(values.get("calibrated"))
        settings["wizard"] = values.get("wizard")
        for field in _FIELDS_WITH_FALLBACK:
            if values.get(field) is not None:
                settings[field] = values[field]
        settings["roast_time_max_s"] = (rows or settings["profile_grid_minutes"]) * 60
        settings["finished_weight_min_g"] = 1  # domain rule: 0 < finished < green
        # A roaster's chart opening is its own data; null means no synthetic ramp.
        for field in _CHART_FIELDS:
            settings[field] = values.get(field)
        for field in (
            "start_model",
            "preheat_temp",
            "charge_temp",
            "cooling_coast_seconds",
            "min_gap_between_roasts_min",
        ):
            settings[field] = values.get(field)
        settings["min_gap_stated"] = values.get(
            "min_gap_between_roasts_min"
        ) is not None and "min_gap_between_roasts_min" not in (
            values.get("inferred") or []
        )
        if values.get("has_temp_readout") is False:
            # No readout: no unit or range is invented and no temperature grid is shown.
            settings["has_temp_readout"] = False
            settings["temp_unit"] = None
            settings["temp_source"] = "none"
            settings["temp_min"] = None
            settings["temp_max"] = None
            settings["wizard"] = None  # a wizard needs a temperature grid
        else:
            for field in ("temp_unit", "temp_source", "temp_min", "temp_max"):
                if values.get(field) is not None:
                    settings[field] = values[field]

    settings["units"] = TEMP_UNITS.get(settings["temp_unit"])
    return settings


def chart_opening(settings):
    """Where the live chart's target curve begins, or None to begin at the first target.

    A roaster with chart anchors (the SR machines) gets their synthetic ramp. A
    preheat-and-charge roaster with a stated charge (or else preheat) temperature starts
    the curve there. Nothing else is invented: with no known opening the curve simply
    starts at the profile's first target, since no source describes a turning point.
    """
    if settings["chart_start_temp"] is not None:
        return {
            "startTemp": settings["chart_start_temp"],
            "inflectionMin": settings["chart_inflection_min"],
            "inflectionTemp": settings["chart_inflection_temp"],
        }
    if settings["start_model"] == "preheat_charge":
        start_temp = settings["charge_temp"]
        if start_temp is None:
            start_temp = settings["preheat_temp"]
        if start_temp is not None:
            return {
                "startTemp": start_temp,
                "inflectionMin": None,
                "inflectionTemp": None,
            }
    return None


def migrate_roaster_ids(roasters, profiles, records, default_roaster_id):
    """Assign a roaster to every profile and record that has none. Idempotent.

    A profile with no roaster gets `default_roaster_id`. A record with no roaster takes
    its profile's roaster (or the default when the profile is gone), and every record
    gets the temperature unit in effect. Returns (profiles_changed, records_changed) so
    the caller only rewrites the files that changed. Does nothing if the default roaster
    is not in `roasters`.
    """
    if default_roaster_id not in roasters:
        return False, False
    profiles_changed = records_changed = False
    for profile in profiles.values():
        if not profile.get("roaster_id"):
            profile["roaster_id"] = default_roaster_id
            profiles_changed = True
    for record in records.values():
        if not record.get("roaster_id"):
            profile = profiles.get(record.get("roast_profile_id")) or {}
            record["roaster_id"] = profile.get("roaster_id") or default_roaster_id
            records_changed = True
        if "temp_unit" not in record:
            record["temp_unit"] = settings_for(roasters, record["roaster_id"])[
                "temp_unit"
            ]
            records_changed = True
    return profiles_changed, records_changed


def migrate_profile_styles(profiles, records):
    """Give every profile and record that predates styles the drip style. Idempotent.

    A record takes its profile's style (drip when the profile is gone). Returns
    (profiles_changed, records_changed) so the caller only rewrites the files that changed.
    """
    profiles_changed = records_changed = False
    for profile in profiles.values():
        if "style" not in profile:
            profile["style"] = DEFAULT_PROFILE_STYLE
            profiles_changed = True
    for record in records.values():
        if "profile_style" not in record:
            record["profile_style"] = profile_style(
                profiles.get(record.get("roast_profile_id"))
            )
            records_changed = True
    return profiles_changed, records_changed
