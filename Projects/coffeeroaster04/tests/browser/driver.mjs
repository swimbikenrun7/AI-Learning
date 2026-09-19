// Drives headless Chromium over the DevTools protocol and prints what it observed as JSON.
// Uses Node's built-in WebSocket (Node 22+): no npm packages and no build step.
//
// usage: node driver.mjs <chromium-debug-port> <base-url>
//
// This only observes; test_browser.py decides what is right. Each scenario records the
// console problems (exceptions, console errors/warnings, failed loads) seen while it ran,
// and a scenario that throws is recorded as {error} so one failure doesn't hide the rest.

const [, , debugPort, baseUrl] = process.argv;

const targets = await (await fetch(`http://127.0.0.1:${debugPort}/json`)).json();
const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
await new Promise((resolve) => (ws.onopen = resolve));

let nextId = 1;
const pending = new Map();
const eventWaiters = new Map();
let problems = [];

ws.onmessage = (message) => {
  const msg = JSON.parse(message.data);
  if (msg.id && pending.has(msg.id)) {
    pending.get(msg.id)(msg);
    pending.delete(msg.id);
    return;
  }
  const waiting = eventWaiters.get(msg.method);
  if (waiting?.length) waiting.shift()(msg.params);
  if (msg.method === "Runtime.exceptionThrown") {
    const details = msg.params.exceptionDetails;
    problems.push("exception: " + (details.exception?.description || details.text));
  } else if (msg.method === "Runtime.consoleAPICalled") {
    if (["error", "warning"].includes(msg.params.type)) {
      const text = msg.params.args.map((arg) => arg.value ?? arg.description).join(" ");
      problems.push(`console.${msg.params.type}: ${text}`);
    }
  } else if (msg.method === "Log.entryAdded") {
    const entry = msg.params.entry;
    if (["error", "warning"].includes(entry.level)) {
      problems.push(`log.${entry.level}: ${entry.text} ${entry.url || ""}`);
    }
  }
};

const send = (method, params = {}) =>
  new Promise((resolve, reject) => {
    const id = nextId++;
    pending.set(id, (msg) => (msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result)));
    ws.send(JSON.stringify({ id, method, params }));
  });

const once = (method) =>
  new Promise((resolve) => {
    if (!eventWaiters.has(method)) eventWaiters.set(method, []);
    eventWaiters.get(method).push(resolve);
  });

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function ev(expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) {
    throw new Error(`evaluating ${expression}: ${result.exceptionDetails.exception?.description}`);
  }
  return result.result.value;
}

async function waitFor(expression, timeoutMs = 10000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await ev(expression)) return;
    await sleep(50);
  }
  throw new Error(`timed out waiting for: ${expression}`);
}

// Navigation resolves when the load event fires, i.e. after every script (Chart.js included) has run.
async function visit(path) {
  const loaded = once("Page.loadEventFired");
  await send("Page.navigate", { url: baseUrl + path });
  await loaded;
}

async function clickAndWaitForLoad(selector) {
  const loaded = once("Page.loadEventFired");
  await ev(`document.querySelector(${JSON.stringify(selector)}).click()`);
  await loaded;
}

const click = (id) => ev(`document.getElementById(${JSON.stringify(id)}).click()`);
const text = (id) => ev(`document.getElementById(${JSON.stringify(id)}).textContent`);
const CLOCK_RUNNING = "document.getElementById('clock-readout').textContent !== '0:00'";

await send("Runtime.enable");
await send("Page.enable");
await send("Log.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1400, height: 900, deviceScaleFactor: 1, mobile: false });

const out = {};
async function scenario(name, body) {
  problems = [];
  try {
    out[name] = await body();
  } catch (error) {
    out[name] = { error: String(error) };
  }
  out[name].problems = problems;
}

// ---- Add Roast: what the page shows, then the timer, First Crack button, and pull countdown ----
async function addRoast(path) {
  await visit(path);
  const state = {
    chartLibLoaded: await ev("typeof Chart !== 'undefined'"),
    graphHidden: await ev("document.querySelector('.roast-graph').hidden"),
    layoutHeightSet: await ev("!!document.querySelector('.roast-layout').style.height"),
    actualTempInputs: await ev("document.querySelectorAll('[name^=actual_temp_]').length"),
    tableHeaders: await ev("Array.from(document.querySelectorAll('.roast-form th')).map((th) => th.textContent.trim())"),
    hints: await ev("Array.from(document.querySelectorAll('.roast-form small')).map((s) => s.textContent.trim())"),
    startConditionOptions: await ev("Array.from(document.querySelectorAll('[name=start_condition] option')).map((o) => o.textContent.trim())"),
    ambientLabel: await ev("document.querySelector('[name=ambient_temp]')?.closest('label').textContent.trim().replace(/\\s+/g, ' ') ?? null"),
    targetReference: await ev("document.querySelector('.target-reference')?.innerText.replace(/\\s+/g, ' ').trim() ?? null"),
    targetReadoutHidden: await ev("document.getElementById('target-temp-readout').hidden"),
    targetReadout: await text("target-temp-readout"),
    rorReadoutInitial: await text("ror-readout"),
    notes: await ev("Array.from(document.querySelectorAll('.roast-note')).map((n) => n.textContent.trim())"),
    clock: await text("clock-readout"),
    pullCountdownHidden: await ev("document.getElementById('pull-countdown').hidden"),
    hasFahrenheit: await ev("document.body.innerText.includes('°F')"),
    hasCelsius: await ev("document.body.innerText.includes('°C')"),
    chartShape: await ev("(() => { const c = document.getElementById('live-chart'); return c.clientWidth ? c.clientHeight / c.clientWidth : null; })()"),
    chart: await ev(`(() => {
      const chart = Chart.getChart('live-chart');
      if (!chart) return null;
      return {
        datasets: chart.data.datasets.length,
        curvePoints: chart.data.datasets[0].data.length,
        curveStart: chart.data.datasets[0].data.slice(0, 4),
        rorStart: chart.data.datasets[2].data.slice(0, 3),
        xMax: chart.options.scales.x.max,
        yTitle: chart.options.scales.y.title.text,
        y1Title: chart.options.scales.y1.title.text,
      };
    })()`),
  };
  // Date field auto-formatting.
  await ev(`(() => {
    const input = document.getElementById('date-input');
    input.value = '09192026';
    input.dispatchEvent(new Event('input', { bubbles: true }));
  })()`);
  state.dateFormatted = await ev("document.getElementById('date-input').value");
  // Timer.
  await click("start-stop-btn");
  await waitFor(CLOCK_RUNNING);
  state.running = {
    button: await text("start-stop-btn"),
    clock: await text("clock-readout"),
    targetReadout: await text("target-temp-readout"),
    rorReadout: await text("ror-readout"),
  };
  // First Crack Now! fills the field and, if the profile has a target development time, starts the countdown.
  await click("mark-first-crack-btn");
  state.firstCrackValue = await ev("document.getElementById('first-crack-input').value");
  if (await ev("!!document.querySelector('.target-reference')?.innerText.includes('development')")) {
    await waitFor("!document.getElementById('pull-countdown').hidden", 5000);
    state.pullCountdown = await text("pull-countdown");
  }
  await click("start-stop-btn");
  state.afterStop = await text("start-stop-btn");
  await click("reset-btn");
  state.afterReset = await text("clock-readout");
  return state;
}

await scenario("addRoastSr800", () => addRoast("/roasts/new/p-sr800"));
await scenario("addRoastCelsius", () => addRoast("/roasts/new/p-kaffelogic"));
await scenario("addRoastGeneCafe", () => addRoast("/roasts/new/p-genecafe"));
await scenario("addRoastNoReadout", () => addRoast("/roasts/new/p-whirley"));
await scenario("addRoastPreheatCharge", () => addRoast("/roasts/new/p-hottop"));
await scenario("addRoastCoast", () => addRoast("/roasts/new/p-quest"));
await scenario("addRoastSr540", () => addRoast("/roasts/new/p-sr540"));

// ---- Profile wizard (offered for the calibrated SR800 only) ----
const readWizardOutput = () =>
  ev(`({
    temps: Array.from(document.querySelectorAll('[name^=temp_]')).map((input) => input.value),
    firstCrack: document.querySelector('[name=target_first_crack]').value,
    developmentTime: document.querySelector('[name=target_development_time]').value,
  })`);

await scenario("wizard", async () => {
  await visit("/profiles/new?roaster=fresh-roast-sr800");
  const state = { panelHiddenAtStart: await ev("document.getElementById('wizard-panel').hidden") };
  await click("wizard-toggle");
  state.panelShownAfterToggle = await ev("!document.getElementById('wizard-panel').hidden");
  await click("wizard-generate-btn");
  state.defaultInputs = await readWizardOutput();
  await ev(`(() => {
    document.getElementById('wizard-density').value = 'high';
    document.getElementById('wizard-process').value = 'natural';
    document.getElementById('wizard-roast-level').value = 'Vienna Roast';
    document.getElementById('wizard-fc-temp').value = '415';
    document.getElementById('wizard-generate-btn').click();
  })()`);
  state.otherInputs = await readWizardOutput();
  return state;
});

// The wizard for any roaster with wizard data: what the panel shows, then what Generate fills in.
async function wizardPage(path) {
  await visit(path);
  const state = {
    tempInputs: await ev("document.querySelectorAll('[name^=temp_]').length"),
    fcTempInput: await ev("document.getElementById('wizard-fc-temp')?.value ?? null"),
  };
  await click("wizard-toggle");
  // innerText leaves out hidden elements, so read the panel's text only once it is open.
  state.notice = await ev("document.body.innerText.includes('Estimated for this roaster')");
  state.noCurveMessage = await ev("document.body.innerText.includes('No temperature curve for this roaster')");
  await click("wizard-generate-btn");
  state.washed = await readWizardOutput();
  await ev(`(() => {
    document.getElementById('wizard-process').value = 'natural';
    document.getElementById('wizard-generate-btn').click();
  })()`);
  state.natural = await readWizardOutput();
  return state;
}

await scenario("wizardEstimatedCurve", () => wizardPage("/profiles/new?roaster=fresh-roast-sr540"));
await scenario("wizardTimesOnly", () => wizardPage("/profiles/new?roaster=kaffelogic-nano-7"));
await scenario("wizardLongGrid", () => wizardPage("/profiles/new?roaster=gene-cafe-cbr-101"));
await scenario("wizardNone", async () => {
  await visit("/profiles/new?roaster=whirley-pop-stovetop-popcorn-popper");
  return { toggle: await ev("!!document.getElementById('wizard-toggle')") };
});

await scenario("editProfile", async () => {
  await visit("/profiles/p-sr800");
  return {
    hasWizard: await ev("!!document.getElementById('wizard-toggle')"),
    hasSelect: await ev("!!document.querySelector('select')"),
    hasRoasterInput: await ev("!!document.querySelector('[name=roaster_id]')"),
    showsRoaster: await ev("document.body.innerText.includes('Fresh Roast SR800')"),
    tempInputs: await ev("document.querySelectorAll('[name^=temp_]').length"),
  };
});

// ---- Add a profile: choose the roaster first, then the form for it ----
await scenario("chooser", async () => {
  await visit("/profiles/new");
  const state = {
    optionCount: await ev("document.querySelectorAll('select[name=roaster] option').length"),
    firstOption: await ev("document.querySelector('select[name=roaster] option').textContent"),
    formShownAtStart: await ev("!!document.querySelector('[name=target_first_crack]')"),
  };
  await ev("document.querySelector('select[name=roaster]').value = 'gene-cafe-cbr-101'");
  // The header has its own (Log out) form, so name the chooser's form explicitly.
  await clickAndWaitForLoad("form[action='/profiles/new'] button[type=submit]");
  state.search = await ev("location.search");
  state.formShownAfter = await ev("!!document.querySelector('[name=target_first_crack]')");
  state.roasterInput = await ev("document.querySelector('[name=roaster_id]')?.value ?? null");
  state.showsRoaster = await ev("document.body.innerText.includes('Gene Cafe CBR-101')");
  state.tempInputs = await ev("document.querySelectorAll('[name^=temp_]').length");
  return state;
});

// ---- Roast list: the columns, client-side sort (including the Roaster column), and search ----
await scenario("roastsList", async () => {
  await visit("/roasts");
  const headers = await ev("Array.from(document.querySelectorAll('#roasts-table th')).map((th) => th.textContent.trim())");
  const column = headers.indexOf("Roaster");
  const roasterCells = () => ev(`Array.from(document.querySelectorAll('#roasts-table tbody tr')).filter((row) => !row.hidden).map((row) => row.cells[${column}].textContent.trim())`);
  const clickHeader = (index) => ev(`document.querySelectorAll('#roasts-table th[data-type]')[${index}].click()`);
  const state = { headers, unsorted: await roasterCells() };
  state.scrollHint = await ev("getComputedStyle(document.querySelector('.scroll-hint')).display");
  await clickHeader(column);
  state.ascending = await roasterCells();
  await clickHeader(column);
  state.descending = await roasterCells();
  // Search reads the date, bean name and profile columns, which come before the new one.
  await ev(`(() => {
    const input = document.getElementById('roast-search');
    input.value = 'kaffelogic';
    input.dispatchEvent(new Event('input', { bubbles: true }));
  })()`);
  state.searched = await roasterCells();
  return state;
});

// ---- Roast detail: its own charts and table, in the record's unit ----
async function roastDetail(path) {
  await visit(path);
  return {
    hasTempChart: await ev("!!document.getElementById('temp-chart')"),
    hasFahrenheit: await ev("document.body.innerText.includes('°F')"),
    hasCelsius: await ev("document.body.innerText.includes('°C')"),
    showsRoaster: await ev("/Roaster: /.test(document.body.innerText)"),
    conditions: await ev("document.querySelector('.roast-conditions')?.innerText.replace(/\\s+/g, ' ').trim() ?? null"),
    tableRows: await ev(`(() => {
      const table = Array.from(document.querySelectorAll('table')).find((t) => t.querySelector('th')?.textContent === 'Time');
      return table ? table.querySelectorAll('tbody tr').length : null;
    })()`),
    charts: await ev(`(() => {
      if (typeof Chart === 'undefined' || !Chart.getChart('temp-chart')) return null;
      const temp = Chart.getChart('temp-chart');
      const ror = Chart.getChart('ror-chart');
      return {
        labelCount: temp.data.labels.length,
        datasetLabels: temp.data.datasets.map((d) => d.label),
        tempYTitle: temp.options.scales.y.title.text,
        rorYTitle: ror.options.scales.y.title.text,
      };
    })()`),
  };
}

await scenario("detailSr800", () => roastDetail("/roasts/r-sr800"));
await scenario("detailCelsius", () => roastDetail("/roasts/r-kaffelogic"));
await scenario("detailGeneCafe", () => roastDetail("/roasts/r-genecafe"));
await scenario("detailNoReadout", () => roastDetail("/roasts/r-whirley"));

// ---- Logging a roast through the real form: start condition and ambient temperature ----
// Runs last because it saves a record into the fixture data.
await scenario("submitRoast", async () => {
  await visit("/roasts/new/p-kaffelogic");
  await ev(`(() => {
    const set = (name, value) => { document.querySelector('[name=' + name + ']').value = value; };
    set('date', '09/19/2026');
    set('bean_name', 'Browser Bean');
    set('start_condition', 'cold');
    set('ambient_temp', '60');   // fine in Fahrenheit, impossible in this Celsius roaster
    set('green_weight', '100');
    set('first_crack', '8:00');
    set('roast_time', '10:00');
    set('finished_weight', '85');
  })()`);
  await clickAndWaitForLoad(".roast-form button[type=submit]");
  const rejected = {
    path: await ev("location.pathname"),
    error: await ev("document.querySelector('p[style*=danger]')?.textContent.trim() ?? null"),
    selectedCondition: await ev("document.querySelector('[name=start_condition]').value"),
    ambientValue: await ev("document.querySelector('[name=ambient_temp]').value"),
    beanName: await ev("document.querySelector('[name=bean_name]').value"),
  };
  await ev("document.querySelector('[name=ambient_temp]').value = '21.5'");
  await clickAndWaitForLoad(".roast-form button[type=submit]");
  return {
    rejected,
    savedPath: await ev("location.pathname"),
    conditions: await ev("document.querySelector('.roast-conditions')?.innerText.replace(/\\s+/g, ' ').trim() ?? null"),
    heading: await ev("document.querySelector('h1').textContent.trim()"),
  };
});

// ---- Phone-sized screens (T-11): a 390 x 844 touch device, which honors the viewport tag ----
await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
await send("Emulation.setTouchEmulationEnabled", { enabled: true });

async function phonePage(path, action) {
  await visit(path);
  if (action) await ev(action);
  return ev(`(() => {
    const visible = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && !el.closest('[hidden]') && getComputedStyle(el).visibility !== 'hidden'; };
    const controls = [...document.querySelectorAll('input:not([type=hidden]):not([type=checkbox]), select, textarea, .btn, .timer-btn, .mark-first-crack-btn, .star-btn, .profile-card__star-btn')].filter(visible);
    const fields = controls.filter((el) => ['INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName));
    const top = (selector) => { const el = document.querySelector(selector); return el ? el.getBoundingClientRect().top + window.scrollY : null; };
    const box = (selector) => { const el = document.querySelector(selector); if (!el || !visible(el)) return null; const r = el.getBoundingClientRect(); return { top: r.top + window.scrollY, bottom: r.bottom + window.scrollY, left: r.left, right: r.right, width: r.width, height: r.height }; };
    return {
      viewportMeta: document.querySelector('meta[name=viewport]')?.content ?? null,
      layoutWidth: document.documentElement.clientWidth,
      pageScrollsSideways: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      fieldsUnder16px: fields.filter((el) => parseFloat(getComputedStyle(el).fontSize) < 16).map((el) => el.name || el.id || el.tagName),
      controlsUnder44px: controls.filter((el) => el.getBoundingClientRect().height < 43.5).map((el) => (el.name || el.id || el.className || el.tagName) + ' ' + Math.round(el.getBoundingClientRect().height)),
      liveTop: top('.roast-live'), formTop: top('.roast-form'),
      startButton: box('#start-stop-btn'), resetButton: box('#reset-btn'), firstCrackButton: box('#mark-first-crack-btn'),
      dateField: box('.date-field'), datePicker: box('#date-picker'), card: box('.page'), formColumn: box('.roast-form'),
      chartShape: (() => { const c = document.getElementById('live-chart'); return c && c.clientWidth ? c.clientHeight / c.clientWidth : null; })(),
      detailChartShapes: ['temp-chart', 'ror-chart'].map((id) => { const c = document.getElementById(id); return c && c.clientWidth ? c.clientHeight / c.clientWidth : null; }),
      scrollHint: (() => { const h = document.querySelector('.scroll-hint'); return h ? getComputedStyle(h).display : null; })(),
      tableScrolls: (() => { const t = document.querySelector('.table-scroll'); return t ? t.scrollWidth > t.clientWidth : null; })(),
    };
  })()`);
}

await scenario("phoneAddRoast", () => phonePage("/roasts/new/p-sr800"));
await scenario("phoneAddRoastLong", () => phonePage("/roasts/new/p-genecafe"));
await scenario("phoneAddRoastNoReadout", () => phonePage("/roasts/new/p-whirley"));
await scenario("phoneRoasts", () => phonePage("/roasts"));
await scenario("phoneDetail", () => phonePage("/roasts/r-sr800"));
await scenario("phonePicker", () => phonePage("/roasts/new"));
await scenario("phoneProfiles", () => phonePage("/profiles"));
await scenario("phoneChooser", () => phonePage("/profiles/new"));
await scenario("phoneProfileForm", () => phonePage("/profiles/new?roaster=fresh-roast-sr800", "document.getElementById('wizard-toggle').click()"));
await scenario("phoneAbout", () => phonePage("/about"));

// A tablet is wider than the 640 px phone breakpoint, so Add Roast keeps its two-column layout
// there with a narrow form column.
await send("Emulation.setDeviceMetricsOverride", { width: 768, height: 1024, deviceScaleFactor: 2, mobile: true });
await scenario("tabletAddRoast", () => phonePage("/roasts/new/p-sr800"));

console.log(JSON.stringify(out));
ws.close();
process.exit(0);
