"""Per-roaster settings: which limits, units, and grid length apply to a profile.

Pure functions over the roasters dict loaded from data/roasters.json; no Flask, no I/O.
"""

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
}

# Every temperature for a roaster is stored and shown in that roaster's own unit and is
# never converted; the only unit-specific text lives here, so no template or script
# carries a literal unit.
TEMP_UNITS = {
    "F": {"symbol": "°F", "ror": "°F/min"},
    "C": {"symbol": "°C", "ror": "°C/min"},
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
