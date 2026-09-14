# Mission 1.4 — Conductor Sizing and the Problem of Code Tables

String sizing was familiar territory. You said so yourself: you already knew the variables before you did the hand calc. Conductor sizing is not — you named it in 1.2 as the place you'd be most likely to build from a mental model instead of from the code.

So this mission does two things at once. It produces a conductor sizing calculation, and it tests a claim you made.

In 1.2 you wrote:

> Wouldn't proper research of a code preclude this sort of thing?

Maybe. Part 1 finds out.

There's also a new software problem here that string sizing didn't have. Conductor sizing runs on **tables** — ampacities, correction factors, adjustment factors — and a table is neither a datasheet parameter nor a constant. It's the "mini database" you described in your 1.1 Q3 answer, arriving for real.

**Target time: 2 hours.** No code this mission.

---

## Mission objective

1. A tested prediction about your own blind spots
2. A conductor sizing hand calculation in `hand_calcs/conductor_sizing.md`
3. A decision about how code tables are represented and stored
4. An honest account of what the research changed

---

# Part 1 — Predict first

**Do this before opening the NEC.** It takes ten minutes and it's the only part of the mission that can't be redone once you've read ahead.

In `hand_calcs/conductor_sizing.md`, under a heading `## Prediction (written before research)`, write down:

1. The inputs you think a conductor sizing calculation requires
2. The steps you think it takes, in order
3. Which code sections you think govern
4. Your confidence, 1–5

Be specific. "Current and temperature" is not a prediction; a named list of values with units is.

Commit this before proceeding:

```bash
git add hand_calcs/conductor_sizing.md
git commit -m "Conductor sizing: prediction before research"
```

The commit is the point. It timestamps the prediction so you can't unconsciously revise it after learning the answer — which everyone does, and which is why the commit exists rather than a promise to be honest.

---

# Part 2 — Research

Now read the code.

Scope this to **one circuit type** — I'd suggest the PV source circuit, from module to combiner or inverter input. Not the inverter output circuit, not the feeder, not the service. One circuit, done properly, beats three done partially, and the second and third will be much faster once the first is verified.

You're looking for the answer to: *given this array and this equipment, what conductor size is code-compliant, and what governs it?*

Things the calculation will likely need, stated as categories rather than sections so you have to find them yourself:

```text
what current the conductor must carry, and how that
  current is derived from datasheet values

base ampacity of a given conductor size and insulation type

correction for ambient temperature

correction for conductors bundled together

any adder for conductors in or on a rooftop

limits imposed by the temperature rating of the terminals
  at each end, independent of the conductor itself

overcurrent protection sizing, and how it interacts
  with all of the above
```

Record, for each: the section number, the edition, and whether it produced a formula or a table lookup. You'll want that inventory in Part 5.

One thing worth watching: at least one of these has changed between recent NEC editions. If you find yourself reading guidance that cites a section number you can't locate in the 2023 text, that's the finding — note it rather than assuming you misread.

---

# Part 3 — Diff your prediction

Under `## What the research changed`, answer honestly:

* What did you predict that turned out to be wrong?
* What did the actual method require that you hadn't anticipated at all?
* What did you predict that doesn't exist?
* Was your confidence rating calibrated?

This section is the mission's most valuable output. Not because you'll be wrong — you may not be — but because the *size* of the gap tells you how much you can trust your own judgment in domains you haven't researched yet. That number is directly relevant to how much agent output you can safely check.

If the gap is near zero, your 1.2 claim was right and we both learn something about how to aim these missions. If it isn't, you've found the failure mode before it cost you anything.

---

# Part 4 — The hand calculation

Same discipline as `string_sizing.md`. A variables table with source, units, and your three-bucket classification. Every step shown. Units at every step.

Use your real equipment and your real site conditions.

Two things to watch that string sizing didn't have:

**Order of operations matters here.** Corrections and adjustments compose, and applying them in the wrong sequence — or to the wrong base value — produces a plausible wrong answer. Write the order down explicitly as part of the method, not just the arithmetic.

**There are likely two independent limits**, and the governing one may not be the one you expect. When a calculation has multiple ceilings, record *which one governs and by how much* — that margin is what tells you whether a design change will move the answer.

End with a stated result: conductor size, insulation type, and the OCPD rating.

---

# Part 5 — How tables live

This is the new engineering-software problem, and it's yours to decide.

Your calculation now depends on values that are neither datasheet parameters nor single constants. They're tables: you look up a row and a column and get a number.

Take the inventory from Part 2 and decide, for each table:

```text
where does it live?
  a Python dict in limits.py
  a JSON file in data/codes/
  something else

how is it keyed?
  what do you pass in to get a value out

what happens at values between rows?
  interpolate, round conservatively, or reject

what happens outside the table's range?

how is the code edition recorded?
```

That last one is the reason this is a domain decision rather than a programmer's. A 2023 ampacity table and a 2026 ampacity table are different data with identical shape. If the edition isn't part of how the data is stored, nothing in the program can tell them apart, and you'll have no way to answer "what changes under the new code" — the exact question you identified in 1.1 Q3.

Write the decision into `docs/domain-decisions.md`. Don't build it yet.

**One constraint I'll impose:** do not transcribe an entire NEC table. Transcribe only the rows and columns your calculation actually touches, and note what you omitted. A full table is hours of error-prone data entry to support a calculation that uses four cells, and hand-transcribed code tables are a well-known source of silent errors in this kind of software. Transcribe what you need, and open an OQ about how a complete table would be sourced and verified if you ever need one.

---

# Part 6 — Update the model

Your Part 4 calculation probably consumed module parameters that `PVModule` doesn't carry — `isc` at minimum, possibly others.

Add only what the calculation used, same rule as 1.2. Update the fixture. Run the existing tests to confirm nothing broke.

If the calculation needed equipment parameters that don't belong on a module or an inverter, that's a finding — say what they belong to rather than forcing them onto an existing class.

---

# What we're *not* doing yet

* No conductor sizing code
* No table lookup implementation
* No voltage drop calculation
* No other circuit types
* No asking an agent what the NEC requires

That last one deserves a sentence. Models are confidently wrong about code requirements, mix editions, and cite sections that don't say what they're claimed to say. You are a PE and this is a safety calculation in your own house. Read the code.

---

# Challenge Questions

### 1. The prediction
Quantify the gap. Did research preclude the failure mode you described in 1.2, or not? Answer the question you asked me, with your own evidence.

### 2. Composition
Your calculation applied more than one correction. State the order and why it's that order. Then describe what a plausible wrong order would produce — a wrong number, or an error?

### 3. What governs
Name the limit that governed your result and the margin to the next one. If a future design change moved the governing limit, which would take over?

### 4. Tables as data
You decided where tables live and how they're keyed. Argue the case for the option you rejected. Under what conditions would it have been the better choice?

### 5. Edition
Describe concretely what you would have to do, in your chosen structure, to answer: "what does this design look like under the 2026 NEC?" If the answer is "re-enter everything," say so.

### 6. Transcription risk
You transcribed table values by hand. That's a manual data entry step inside a safety calculation. How would you verify the transcription is correct — and is that a test, a review, or something else?

---

## One rule for this mission

**Read the code before you write the calculation, and write down what you expected first.**

You already believe the first half. The second half is what turns a habit into evidence — and evidence about your own calibration is worth more here than the conductor size, because you'll be using that calibration every time you decide whether to check an agent's work or trust it.
