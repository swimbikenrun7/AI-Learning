(function () {
  document.getElementById("wizard-toggle").addEventListener("click", () => {
    const panel = document.getElementById("wizard-panel");
    panel.hidden = !panel.hidden;
  });

  // Roast-level DTRs use the same six-tier vocabulary as
  // calculations.py's classify_roast, so the wizard speaks the same
  // language as the rest of the app. Scaled from a real logged Fresh
  // Roast result (medium density, washed: 1:10 development time off a
  // 6:15 first crack landed at Full City, i.e. ~15.7% DTR) by the
  // same factor across all six tiers, preserving the relative
  // progression of a commonly published drum-roaster DTR table
  // (light ~16%, dark ~31%) while anchoring the absolute scale to
  // this machine - see SPEC.md's Profile Wizard section.
  const ROAST_LEVEL_DTR = {
    "City Roast": 0.12,
    "City Plus": 0.13,
    "Full City": 0.16,
    "Full City Plus": 0.18,
    "Vienna Roast": 0.2,
    "Italian Roast": 0.23,
  };

  // Time to first crack, by density (seconds). Deriving this from
  // (entered first-crack temp - a fixed start temp) / a density pace,
  // as an earlier version did, conflated two unrelated things: how
  // hot your probe reads at crack (which legitimately varies a lot by
  // bean/instrument/altitude) and how long Maillard actually takes
  // (which, per real-world Fresh Roast use, barely varies with
  // density) - a high-altitude bean entered at a much higher FC temp
  // produced a wildly inflated multi-minute estimate instead of the
  // ~30s difference actually observed. These are direct time targets
  // instead, anchored to one real logged result (medium/washed: 6:15)
  // plus the user's own rule of thumb for the deltas - see SPEC.md.
  const MAILLARD_TIME_SECONDS = { low: 375, medium: 375, high: 405 };
  const NATURAL_TIME_ADJUST_SECONDS = 20;

  // The profile grid starts at minute 1, not at charge: the live
  // Add Roast graph already models the steep charge-to-drying ramp
  // (145 start, 270 by 30s, in the roaster's own unit) outside the saved profile, so by
  // minute 1 a roast is already just past drying and into early
  // Maillard - see add_roast.html's START_TEMP/INFLECTION constants.
  const PROFILE_START_TEMP = 315;

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  // Spreads a phase's total temperature rise across its minutes
  // with a larger share up front and a smaller share at the end,
  // so the rate of rise steadily declines within the phase instead
  // of staying flat or spiking - the "no crash, no flick" guidance
  // (a flat/rising RoR risks baked or ashy flavor). Used for the
  // Maillard phase, which typically has enough minutes for this
  // shape to matter.
  function decelerate(startTemp, endTemp, steps) {
    const totalRise = endTemp - startTemp;
    const weights = [];
    for (let i = 0; i < steps; i++) weights.push(steps - i);
    const weightSum = weights.reduce((a, b) => a + b, 0);
    const temps = [];
    let current = startTemp;
    for (let i = 0; i < steps; i++) {
      current += (totalRise * weights[i]) / weightSum;
      temps.push(Math.round(current));
    }
    return temps;
  }

  // Mirrors app.py's format_mm_ss so wizard-filled fields match the
  // rest of the app's MM:SS convention.
  function formatMmSs(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${String(seconds).padStart(2, "0")}`;
  }

  document.getElementById("wizard-generate-btn").addEventListener("click", () => {
    const density = document.getElementById("wizard-density").value;
    const process = document.getElementById("wizard-process").value;
    const roastLevel = document.getElementById("wizard-roast-level").value;
    const fcTemp = Number(document.getElementById("wizard-fc-temp").value);

    // Time to first crack comes from density/process alone; entered
    // fcTemp only shapes where the curve ends (below), not how long
    // it takes to get there.
    const fcSeconds =
      MAILLARD_TIME_SECONDS[density] +
      (process === "natural" ? NATURAL_TIME_ADJUST_SECONDS : 0);
    // Whole-minute grid index (the profile's 12-point grid has no
    // sub-minute granularity - see SPEC.md's domain rules), used only
    // to place the Maillard curve's temp-grid points.
    const fcMinute = clamp(Math.round(fcSeconds / 60), 2, 9);

    // The temp curve only models Maillard (minute 1 to first crack);
    // what happens after is a target development *time*, not a target
    // temperature - see SPEC.md's Profile Wizard section.
    const dtr = ROAST_LEVEL_DTR[roastLevel];
    const developmentSeconds = Math.round((fcSeconds * dtr) / (1 - dtr));

    const temps = new Array(12).fill("");
    temps[0] = PROFILE_START_TEMP;
    decelerate(PROFILE_START_TEMP, fcTemp, fcMinute - 1).forEach((temp, i) => {
      temps[1 + i] = temp;
    });

    for (let minute = 1; minute <= 12; minute++) {
      document.querySelector(`[name="temp_${minute}"]`).value = temps[minute - 1];
    }
    document.querySelector('[name="target_first_crack"]').value = formatMmSs(fcSeconds);
    document.querySelector('[name="target_development_time"]').value =
      formatMmSs(developmentSeconds);
  });
})();
