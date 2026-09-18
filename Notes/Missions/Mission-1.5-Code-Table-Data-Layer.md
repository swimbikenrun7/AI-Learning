# Mission 1.5 — The Code Table Data Layer

Every calculation so far has run on numbers you typed directly into a function call. Conductor sizing can't. It runs on tables, and tables live in files.

This mission builds the layer between the two: JSON on disk, functions that read it, and — before either of those is trusted — a script that checks the data has the shape physics requires.

That last part is the one that matters most, and it's the answer to your own Mission 1.4 Q6. You correctly identified that a unit test asserting `ampacity("10 AWG", 90) == 40` proves only that the code reads what you typed. The structural check is different: it verifies properties that must hold for *any* correct ampacity table, without ever consulting the source. It catches the errors your eye slides past.

**Target time: 2 hours.** The transcription is the long pole. Scope it as described in Part 1 and don't let it eat the mission.

---

## Mission objective

1. One NEC table transcribed to `data/codes/nec-2023.json` with metadata
2. A structural verification script in `tools/verify_tables.py`
3. Lookup functions in `calcs/codes.py`
4. Tests for the lookups
5. A decision about conductor size ordering

---

# Part 1 — Transcribe one table

**Table 310.16, copper conductors, 60/75/90 °C columns.** Complete — you argued in 1.4 that whole tables beat trimmed ones and I conceded. Skip the aluminum section for now; note the omission.

Do not transcribe the other tables this mission. Build the entire pipeline around one table first, verify it works end to end, then the rest are repetition you can do in twenty minutes or hand off.

Structure, per the shape decision from 1.4:

```json
{
  "code": "NEC",
  "edition": "2023",
  "source": "NFPA 70-2023",
  "transcribed_by": "JAG",
  "transcribed_date": "2026-09-18",
  "tables": {
    "310.16": {
      "description": "Ampacities of insulated conductors rated up to 2000V",
      "units": "A",
      "conditions": "Not more than three current-carrying conductors in raceway, cable, or earth; ambient 30°C",
      "omitted": "Aluminum and copper-clad aluminum columns not transcribed",
      "copper": {
        "14": {"60": 15, "75": 20, "90": 25},
        "12": {"60": 20, "75": 25, "90": 30},
        "10": {"60": 30, "75": 35, "90": 40}
      }
    }
  }
}
```

The `conditions` field is not decoration. Table 310.16 values are only valid under stated assumptions, and a lookup function that returns 40 without them invites someone — you, an agent, a future collaborator — to use the number where it doesn't apply.

**Keys are strings.** `"10"` not `10`. JSON object keys are always strings anyway, and "1/0" and "4/0" can't be integers at all. Deciding this now avoids a type inconsistency later.

---

# Part 2 — Verify the data before trusting it

Create `tools/verify_tables.py`. Run it before you write a single lookup.

This script asserts properties that must hold for any correct ampacity table:

```text
monotonic in conductor size
  — a larger conductor never carries less current

monotonic in temperature rating
  — 90°C ampacity >= 75°C >= 60°C, for every row

no missing cells
  — every size has all three temperature columns

plausible ratios
  — the 90°C/60°C ratio should sit in a narrow band
    across every row; an outlier is a transcription error
```

That last check is the one that earns its keep. A transposed digit — 40 entered as 04, or 55 as 50 — usually preserves monotonicity and fails the ratio check.

`tools/` is a new folder: things you run, that aren't part of the application and aren't tests. Add it to your "where things live" table.

Run it. If it passes on the first try, deliberately corrupt one value, confirm the script catches it, and put it back. A verification script that has never failed is not known to work.

---

# Part 3 — The ordering problem

Your hand calc says "select next lowest wire gauge (larger wire)." Implementing that requires the program to know which conductor is next, and that is genuinely harder than it looks:

```text
14, 12, 10, 8, 6, 4, 3, 2, 1, 1/0, 2/0, 3/0, 4/0, 250, 300, 350 ...
```

Numbers descend, then invert into aught notation, then switch to kcmil ascending. Sorting these correctly cannot be done by parsing the string as a number, and it's a place an agent will produce something that looks right and orders 1/0 next to 1.

Decide how you're representing this. Options worth weighing:

* an explicit ordered list, smallest to largest
* keying on circular mils from Chapter 9 Table 8
* a sort key computed from the designation

The explicit list is the least clever and the easiest to verify by eye against the code book. Cleverness is worth very little here and correctness is worth a lot — but make the choice deliberately and write the reason down.

Wherever it lives, `next_larger_conductor("12")` returning `"10"` is what the sizing loop will call in 1.6.

---

# Part 4 — Lookup functions

Create `calcs/codes.py`. Two distinct kinds of lookup, and conflating them is a real hazard:

**Exact-key lookup.** Ampacity takes a conductor size and a temperature rating that must match a column exactly. `90` is a column; `85` is not a column and is not an error to interpolate — it's an error to ask.

**Range lookup.** Temperature correction factors are keyed by an ambient *band* — your 66.3 °C fell in a 66–70 °C row. The input is continuous, the table is discrete, and something has to decide which row applies.

Write the ampacity lookup this mission:

```python
def ampacity(size: str, temp_rating: int,
             material: str = "copper",
             edition: str = "2023") -> float:
    """Base ampacity from NEC Table 310.16.

    Values assume not more than three current-carrying conductors
    and 30°C ambient. Correction and adjustment factors are applied
    separately by the caller.

    Raises:
        KeyError: if the size or temperature rating is not in the table

    Reference: hand_calcs/conductor_sizing.md
    """
```

Two things to get right.

**Raise, don't return a default.** A lookup that can't find its key must fail loudly. Returning `None` or `0` produces a downstream calculation that runs to completion and yields a wrong conductor size — which is worse than a crash, because a crash gets investigated.

**Load the file once, not per call.** Reading JSON on every lookup is slow and, more importantly, means the data can change mid-calculation. Module-level load or a cached loader; either is fine, but decide rather than defaulting.

The range lookup for temperature correction goes in 1.6, alongside the table it needs. Note the design question now, though: when the ambient falls exactly on a band boundary, which row wins? That's a domain decision and the answer is not obvious.

---

# Part 5 — Tests

`tests/test_codes.py`:

```text
a known value from the book        ampacity("10", 90) == 40
a second known value               ampacity("14", 60) == 15
an unknown size raises             ampacity("99", 90) → KeyError
an unknown temp rating raises      ampacity("10", 85) → KeyError
ordering works                     next_larger_conductor("12") == "10"
ordering across the aught boundary next_larger_conductor("1") == "1/0"
```

That last one is the test worth writing. It's the case that breaks naive implementations, and it will still be there checking when someone refactors the ordering logic in two years.

Note what these tests are and aren't. They verify the *plumbing* — that lookups find what's in the file and fail when they should. They do not verify the transcription. That's Part 2's job, and the two are not interchangeable.

---

# What we're *not* doing yet

* No conductor sizing calculation
* No upsizing loop
* No temperature correction or adjustment factor lookups
* No other tables
* No interpolation of any kind

---

# Challenge Questions

### 1. Two kinds of checking
Your structural verification script and your lookup tests both pass. Describe a specific transcription error that neither catches. What would catch it?

### 2. Failing loudly
You made `ampacity` raise on an unknown key. Construct the concrete scenario where returning `0` instead would have produced a wrong conductor size that passes every test you wrote in Mission 1.3 and 1.5.

### 3. Conditions
The `conditions` field records assumptions that make the table's values valid. Right now nothing enforces them — the function returns 40 A whether or not the installation matches. Is that acceptable? What would enforcement look like, and what would it cost?

### 4. Ordering
State your representation and why. Then: if an agent were handed "implement next_larger_conductor" with no further guidance, what specifically would you check first in its output?

### 5. The boundary
Temperature correction bands are ranges, and an ambient landing exactly on a boundary belongs to one row or the other. Which, and why? Frame the answer in terms of which direction is conservative, not which is conventional.

### 6. Edition as a parameter
`ampacity` takes `edition="2023"` as a default. Walk through what actually happens when you add `nec-2026.json` — every file that changes, every decision that surfaces. You wrote in 1.4 that the hard problem is method discontinuity rather than data swapping. Does this design help with that, or only with the easy half?

---

## One rule for this mission

**Verify the data before you write anything that depends on it.**

You transcribed those numbers by hand from a book, at some hour of the evening, one row at a time. Every calculation in this project will eventually rest on them, and no amount of correct code compensates for a wrong cell. The structural script is the cheapest insurance available and it runs in under a second forever.

This is the software equivalent of checking your inputs before running the model — which you've done your entire career, on the grounds that a beautifully executed analysis of the wrong numbers is worse than no analysis, because it comes with confidence attached.
