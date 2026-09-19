const roastConfig = JSON.parse(document.getElementById("roast-config").textContent);
const profileTemps = roastConfig.profileTemps;
const targetDevelopmentSeconds = roastConfig.targetDevelopmentSeconds;
// One profile row per minute, so the x-axis runs 0..rowCount.
const rowCount = roastConfig.rows;
// The roaster's own unit ({symbol, ror}); no temperature is ever converted.
const units = roastConfig.units;
// The chart's opening for this roaster: {startTemp, inflectionMin, inflectionTemp}
// (start temp is the roaster's starting/preheat temp, not ambient room temp; the
// inflection is expressed in minutes to match the x-axis), or null for no synthetic ramp.
const anchors = roastConfig.anchors;

// Monotone cubic Hermite interpolation (Fritsch-Butland/PCHIP): unlike a
// natural spline this never overshoots between knots, so the curve stays
// increasing throughout instead of wobbling. Interior tangents use a
// weighted harmonic mean of the two neighboring slopes (not a plain
// average) so a steep segment next to a shallow one doesn't drag the
// curve into a hump - the harmonic mean is pulled toward the shallower
// side instead of splitting the difference. The tangent at the last
// knot is pinned to 0 so the rise eases into the flat hold-line below
// instead of arriving at it with a visible kink.
function buildMonotoneSpline(knots) {
  const n = knots.length;
  const xs = knots.map((k) => k.x);
  const ys = knots.map((k) => k.y);

  const h = [];
  const delta = [];
  for (let i = 0; i < n - 1; i++) {
    h.push(xs[i + 1] - xs[i]);
    delta.push((ys[i + 1] - ys[i]) / h[i]);
  }

  const m = new Array(n);
  // The first knot's tangent can't just be the first secant (delta[0]):
  // a segment's *average* slope always equals its secant regardless of
  // the tangents chosen, so if delta[0] is much steeper than delta[1]
  // (like the initial jump to roasting heat vs. the gentler rise after),
  // pinning m[0] to delta[0] forces the segment to bulge upward in the
  // middle to keep that average - which is exactly the hump. The
  // standard non-centered PCHIP boundary estimate below front-loads m[0]
  // instead, so the segment decelerates the whole way through with no
  // compensating bulge.
  if (n < 3) {
    m[0] = delta[0];
  } else {
    let d0 = ((2 * h[0] + h[1]) * delta[0] - h[0] * delta[1]) / (h[0] + h[1]);
    if (Math.sign(d0) !== Math.sign(delta[0])) {
      d0 = 0;
    } else if (Math.sign(delta[0]) !== Math.sign(delta[1]) && Math.abs(d0) > 3 * Math.abs(delta[0])) {
      d0 = 3 * delta[0];
    }
    m[0] = d0;
  }
  m[n - 1] = 0;
  for (let i = 1; i < n - 1; i++) {
    if (delta[i - 1] === 0 || delta[i] === 0 || delta[i - 1] * delta[i] < 0) {
      m[i] = 0;
    } else {
      const w1 = 2 * h[i] + h[i - 1];
      const w2 = h[i] + 2 * h[i - 1];
      m[i] = (w1 + w2) / (w1 / delta[i - 1] + w2 / delta[i]);
    }
  }

  for (let i = 0; i < n - 1; i++) {
    if (delta[i] === 0) {
      m[i] = 0;
      m[i + 1] = 0;
      continue;
    }
    const alpha = m[i] / delta[i];
    const beta = m[i + 1] / delta[i];
    if (alpha < 0) m[i] = 0;
    if (beta < 0) m[i + 1] = 0;
    const s = alpha * alpha + beta * beta;
    if (s > 9) {
      const tau = 3 / Math.sqrt(s);
      m[i] = tau * alpha * delta[i];
      m[i + 1] = tau * beta * delta[i];
    }
  }

  return function evaluate(x) {
    let i = n - 2;
    for (let k = 0; k < n - 1; k++) {
      if (x >= xs[k] && x <= xs[k + 1]) {
        i = k;
        break;
      }
    }
    const segLength = xs[i + 1] - xs[i];
    const t = (x - xs[i]) / segLength;
    const t2 = t * t;
    const t3 = t2 * t;
    const h00 = 2 * t3 - 3 * t2 + 1;
    const h10 = t3 - 2 * t2 + t;
    const h01 = -2 * t3 + 3 * t2;
    const h11 = t3 - t2;
    return (
      h00 * ys[i] + h10 * segLength * m[i] + h01 * ys[i + 1] + h11 * segLength * m[i + 1]
    );
  };
}

const enteredPoints = profileTemps
  .map((temp, index) => ({ x: index + 1, y: temp }))
  .filter((point) => point.y !== null);

let targetTempAt = null;
let targetRorAt = null;
let chart = null;

if (enteredPoints.length > 0) {
  const lastEntered = enteredPoints[enteredPoints.length - 1];
  const spline = buildMonotoneSpline(
    anchors
      ? [
          { x: 0, y: anchors.startTemp },
          { x: anchors.inflectionMin, y: anchors.inflectionTemp },
          ...enteredPoints,
        ]
      : // No known opening for this roaster: start flat at the first target temperature.
        [{ x: 0, y: enteredPoints[0].y }, ...enteredPoints]
  );

  targetTempAt = function (minutesElapsed) {
    const x = Math.max(0, minutesElapsed);
    // Hold flat once the roast runs past the last minute with an entered
    // target, per the profile's carry-forward domain rule (SPEC.md).
    if (x >= lastEntered.x) return lastEntered.y;
    return spline(x);
  };

  // Rate of rise is the temperature curve's slope - estimated with a
  // small central difference on the same spline used for the curve
  // itself, rather than a second, separately-fit function.
  const RATE_OF_RISE_STEP = 0.01;
  targetRorAt = function (minutesElapsed) {
    const x = Math.max(0, minutesElapsed);
    const before = targetTempAt(Math.max(0, x - RATE_OF_RISE_STEP));
    const after = targetTempAt(x + RATE_OF_RISE_STEP);
    return (after - before) / (2 * RATE_OF_RISE_STEP);
  };

  const curve = [];
  const rorCurve = [];
  for (let x = 0; x <= rowCount; x += 0.1) {
    curve.push({ x, y: targetTempAt(x) });
    rorCurve.push({ x, y: targetRorAt(x) });
  }

  chart = new Chart(document.getElementById("live-chart"), {
    type: "line",
    data: {
      datasets: [
        {
          label: "Target",
          data: curve,
          borderColor: "#7570b3",
          backgroundColor: "#7570b3",
          pointRadius: 0,
          tension: 0,
          yAxisID: "y",
        },
        {
          label: "Now",
          data: [{ x: 0, y: targetTempAt(0) }],
          showLine: false,
          pointRadius: 7,
          pointBackgroundColor: "#d95f02",
          pointBorderColor: "#d95f02",
          yAxisID: "y",
        },
        {
          label: "Rate of rise",
          data: rorCurve,
          borderColor: "#1b9e77",
          backgroundColor: "#1b9e77",
          pointRadius: 0,
          tension: 0,
          yAxisID: "y1",
        },
        {
          label: "RoR now",
          data: [{ x: 0, y: targetRorAt(0) }],
          showLine: false,
          pointRadius: 7,
          pointBackgroundColor: "#d95f02",
          pointBorderColor: "#d95f02",
          yAxisID: "y1",
        },
      ],
    },
    options: {
      animation: false,
      scales: {
        x: {
          type: "linear",
          min: 0,
          max: rowCount,
          title: { display: true, text: "Time (minutes)" },
          ticks: {
            stepSize: 1,
            callback: (value) => formatMinutesClock(value),
          },
        },
        y: { position: "left", title: { display: true, text: `Temperature (${units.symbol})` } },
        y1: {
          position: "right",
          title: { display: true, text: `Rate of rise (${units.ror})` },
          grid: { drawOnChartArea: false },
        },
      },
      plugins: {
        tooltip: {
          callbacks: {
            title: (items) => (items.length ? formatMinutesClock(items[0].parsed.x) : ""),
            label: (item) =>
              `${item.dataset.label}: ${Math.round(item.parsed.y)}${
                item.dataset.yAxisID === "y1" ? units.ror : units.symbol
              }`,
          },
        },
      },
    },
  });

  document.getElementById("target-temp-readout").textContent =
    Math.round(targetTempAt(0)) + units.symbol;
  document.getElementById("ror-readout").textContent =
    Math.round(targetRorAt(0)) + units.ror;
} else {
  document.getElementById("live-chart").hidden = true;
  document.getElementById("no-profile-data").hidden = false;
}

const startStopBtn = document.getElementById("start-stop-btn");
const resetBtn = document.getElementById("reset-btn");
const markFirstCrackBtn = document.getElementById("mark-first-crack-btn");
const firstCrackInput = document.getElementById("first-crack-input");
const clockReadout = document.getElementById("clock-readout");
const targetReadout = document.getElementById("target-temp-readout");
const rorReadout = document.getElementById("ror-readout");

// The clock advances in whole seconds, but the target-temp readout and
// the graph's "Now" marker track real elapsed time continuously (via
// performance.now()) so they glide instead of jumping once a second.
let running = false;
let elapsedMsAtPause = 0;
let resumeTimestamp = 0;
let lastFlashedMinute = 0;
let animationFrameId = null;

function formatClock(totalSeconds) {
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return mins + ":" + String(secs).padStart(2, "0");
}

function formatMinutesClock(minutesValue) {
  return formatClock(Math.round(minutesValue * 60));
}

function currentElapsedMs() {
  return running ? elapsedMsAtPause + (performance.now() - resumeTimestamp) : elapsedMsAtPause;
}

function flashInvert(times = 2) {
  const root = document.documentElement;
  const steps = times * 2;
  for (let i = 0; i < steps; i++) {
    setTimeout(() => {
      root.classList.toggle("inverted", i % 2 === 0);
    }, i * 150);
  }
}

function parseMmSs(value) {
  const match = /^(\d+):([0-5]\d)$/.exec((value || "").trim());
  return match ? Number(match[1]) * 60 + Number(match[2]) : null;
}

const pullCountdownEl = document.getElementById("pull-countdown");
let lastCountdownFirstCrackSeconds = null;
let pullFlashed = false;

function updatePullCountdown(elapsedSeconds) {
  if (!targetDevelopmentSeconds) return;

  const firstCrackSeconds = parseMmSs(firstCrackInput.value);
  if (firstCrackSeconds !== lastCountdownFirstCrackSeconds) {
    pullFlashed = false;
    lastCountdownFirstCrackSeconds = firstCrackSeconds;
  }

  if (firstCrackSeconds === null) {
    pullCountdownEl.hidden = true;
    return;
  }

  pullCountdownEl.hidden = false;
  const remaining = firstCrackSeconds + targetDevelopmentSeconds - elapsedSeconds;
  if (remaining > 0) {
    pullCountdownEl.textContent = "Pull in " + formatClock(remaining);
  } else {
    pullCountdownEl.textContent = "Pull now!";
    if (!pullFlashed) {
      flashInvert(4);
      pullFlashed = true;
    }
  }
}

function updateLiveDisplay() {
  const elapsedMs = currentElapsedMs();
  const elapsedSeconds = Math.floor(elapsedMs / 1000);
  clockReadout.textContent = formatClock(elapsedSeconds);

  const minuteMark = Math.floor(elapsedSeconds / 60);
  if (minuteMark > lastFlashedMinute) {
    flashInvert(2);
    lastFlashedMinute = minuteMark;
  }

  updatePullCountdown(elapsedSeconds);

  if (targetTempAt) {
    const elapsedMinutes = elapsedMs / 60000;
    const clampedMinutes = Math.min(elapsedMinutes, rowCount);
    const temp = targetTempAt(elapsedMinutes);
    const ror = targetRorAt(elapsedMinutes);
    targetReadout.textContent = Math.round(temp) + units.symbol;
    rorReadout.textContent = Math.round(ror) + units.ror;
    chart.data.datasets[1].data = [{ x: clampedMinutes, y: temp }];
    chart.data.datasets[3].data = [{ x: clampedMinutes, y: ror }];
    chart.update("none");
  }
}

function renderFrame() {
  updateLiveDisplay();
  if (running) animationFrameId = requestAnimationFrame(renderFrame);
}

startStopBtn.addEventListener("click", () => {
  if (!running) {
    running = true;
    resumeTimestamp = performance.now();
    animationFrameId = requestAnimationFrame(renderFrame);
    startStopBtn.textContent = "Stop";
    startStopBtn.classList.remove("timer-btn--start");
    startStopBtn.classList.add("timer-btn--stop");
  } else {
    elapsedMsAtPause = currentElapsedMs();
    running = false;
    cancelAnimationFrame(animationFrameId);
    startStopBtn.textContent = "Start";
    startStopBtn.classList.remove("timer-btn--stop");
    startStopBtn.classList.add("timer-btn--start");
  }
});

resetBtn.addEventListener("click", () => {
  cancelAnimationFrame(animationFrameId);
  running = false;
  elapsedMsAtPause = 0;
  lastFlashedMinute = 0;
  pullFlashed = false;
  lastCountdownFirstCrackSeconds = null;
  startStopBtn.textContent = "Start";
  startStopBtn.classList.remove("timer-btn--stop");
  startStopBtn.classList.add("timer-btn--start");
  updateLiveDisplay();
});

markFirstCrackBtn.addEventListener("click", () => {
  firstCrackInput.value = formatClock(Math.floor(currentElapsedMs() / 1000));
});
