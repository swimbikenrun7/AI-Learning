(function () {
  // Everything roaster-specific comes from the page's config (the roaster's `wizard`
  // data in data/roasters.json, see SPEC.md), never from constants in this file:
  //   rows                 how many one-minute profile rows this roaster's grid has
  //   timeToFirstCrack     seconds by bean density ({low, medium, high})
  //   naturalAdjustSeconds change for a natural/honey process (0 if unknown)
  //   dtrByLevel           development-time ratio by roast level, using the same
  //                        six-tier names as calculations.py's classify_roast
  //   startTemp / defaultFirstCrackTemp  in the roaster's own unit; null if unknown
  //   hasCurve             true only if both temperatures are known, otherwise the
  //                        wizard fills just the target times and no temperature curve
  const config = JSON.parse(document.getElementById("wizard-config").textContent);

  document.getElementById("wizard-toggle").addEventListener("click", () => {
    const panel = document.getElementById("wizard-panel");
    panel.hidden = !panel.hidden;
  });

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

    // Time to first crack comes from density/process alone; an entered
    // first-crack temperature only shapes where the curve ends (below), not
    // how long it takes to get there.
    const fcSeconds =
      config.timeToFirstCrack[density] +
      (process === "natural" ? config.naturalAdjustSeconds : 0);

    // Development is a target *time*, not a target temperature - see SPEC.md's
    // Profile Wizard section.
    const dtr = config.dtrByLevel[roastLevel];
    const developmentSeconds = Math.round((fcSeconds * dtr) / (1 - dtr));

    if (config.hasCurve) {
      const fcTemp = Number(document.getElementById("wizard-fc-temp").value);
      // Whole-minute grid index (the profile grid has no sub-minute
      // granularity - see SPEC.md's domain rules), used only to place the
      // Maillard curve's temp-grid points; it stays inside the roaster's rows.
      const fcMinute = clamp(Math.round(fcSeconds / 60), 2, Math.max(2, config.rows - 3));

      // The temp curve only models Maillard (minute 1 to first crack);
      // what happens after is the development time above.
      const temps = new Array(config.rows).fill("");
      temps[0] = config.startTemp;
      decelerate(config.startTemp, fcTemp, fcMinute - 1).forEach((temp, i) => {
        temps[1 + i] = temp;
      });

      for (let minute = 1; minute <= config.rows; minute++) {
        document.querySelector(`[name="temp_${minute}"]`).value = temps[minute - 1];
      }
    }

    document.querySelector('[name="target_first_crack"]').value = formatMmSs(fcSeconds);
    document.querySelector('[name="target_development_time"]').value =
      formatMmSs(developmentSeconds);
  });
})();
