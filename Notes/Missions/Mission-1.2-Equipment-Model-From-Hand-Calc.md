# Mission 1.2 — Deriving a Data Model From a Hand Calculation

OQ-3 asks where module and inverter parameters come from. You wrote your own answer into the "what would settle it" field: do the calculation by hand against a real datasheet and notice which fields you actually reached for.

That's what this mission is. It runs in one direction only:

```text
real datasheet
     ↓
hand calculation
     ↓
notice which fields you touched
     ↓
that is the data model
```

Not the other way around. The common failure — and the one an agent will commit instantly if you let it — is to design a `SolarModule` class first, from imagination, and then discover three calculations later that it's missing the field you need and carries four you never use. A data model derived from a real calculation is the right size by construction.

You will write Python in this mission. Not much, and not until Part 5.

**Target time: 2 hours.**

---

## Mission objective

By the end you should have:

1. Two real datasheets in the repository.
2. A hand-computed cold-weather string sizing calculation, showing work.
3. The pass/fail boundary located by hand.
4. An equipment parameter model written in Python, justified field by field.
5. OQ-3 closed.

And you should understand why a specification written *after* one worked example beats a specification written before any.

---

# Part 1 — Choose real equipment

Pick one module and one inverter you would actually consider installing. Not a textbook example — something currently purchasable, because the datasheet quirks are the point.

Download both datasheets. Commit them:

```bash
mkdir -p docs/datasheets
# move the two PDFs in
git add docs/datasheets
git commit -m "Add reference datasheets for string sizing derivation"
```

Committing vendor PDFs is a deliberate choice. The calculation you're about to do is only reproducible if the exact document you read from is preserved — datasheets get silently revised. This is the same reason a calc package carries its references.

---

# Part 2 — Establish the design temperature

Before touching the datasheet, determine the lowest expected ambient temperature for your site, and the basis for it.

Your code edition specifies a method. Find it, read it, and write down:

* the value you'll use
* the source it came from
* the specific code section that directs you to that source
* the units the source publishes in

That last one matters more than it looks. If the source publishes in °F and the module's temperature coefficient is in %/°C, you have a unit conversion sitting in the middle of a safety calculation. Notice where it lives now, while it's visible, rather than discovering it later inside a function.

I'm not going to tell you what the correct method or value is. That's the left column of your domain decisions table, and it stays there permanently.

---

# Part 3 — The hand calculation

On paper or in a text file, compute:

**(a) Maximum module Voc at the design low temperature.**

Show every step. Write the units at every step. If you find yourself unsure whether a coefficient is a percentage or a fraction, stop and resolve it — that ambiguity is a real defect source and it lives on the datasheet, not in your arithmetic.

**(b) Maximum number of modules per string** such that string Voc stays within the inverter's maximum input voltage.

**(c) Minimum number of modules per string** such that the string stays inside the inverter's MPPT window under high-temperature operating conditions.

For (c) you'll need a high-temperature assumption and a different coefficient than (a) used. Note which assumptions you had to invent because no document gave them to you. Those are future OQs.

**Record every number you read off either datasheet in a running list as you go.** Do not reconstruct this afterward from memory — the whole mission depends on this list being an honest record of what you actually touched.

---

# Part 4 — Find the boundary

You now have a maximum string length. Compute the string Voc at that length, and at that length plus one.

Write down both numbers and the margin to the limit.

Then answer, in writing: **how close is too close?** If the limit is 600 V and your string lands at 597.3 V, is that a pass?

There is no software answer to this question. It is the reason "the tolerance used when comparing two floating-point results" sits in your left column. You just met the concrete case, which is a better time to decide it than in the abstract.

Whatever you decide, that's a domain decision — log it.

---

# Part 5 — Derive the model

Now look at your running list from Part 3.

Write out, as plain text first:

```text
For each value:
  name
  what document it came from
  its units
  is it a fixed property of the equipment, or a design assumption?
```

That last distinction is the one that structures everything. A module's Voc is a property of the module. Your design low temperature is not — it's a property of the site. They will end up in different places, and conflating them is how a program becomes impossible to use for a second project.

Then write it in Python. One file, in the repository:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class PVModule:
    """Parameters read from a module datasheet.

    All temperature coefficients in %/°C. All voltages in volts.
    """
    manufacturer: str
    model: str
    voc_stc: float          # V, open-circuit voltage at STC
    # ... only the fields you actually used in Part 3
```

### Rules

1. **No field goes in that you did not use in Part 3.** If you're tempted, write the temptation down as a note instead.
2. Every field carries a unit in a comment or in the name.
3. `frozen=True` — decide for yourself whether you agree, and write one sentence either way.
4. Do the same for the inverter.
5. Instantiate one of each with your real equipment's values and commit it.

No calculation logic yet. Just the containers, and one real instance of each.

---

# Part 6 — Close OQ-3

Write the resolution. Then answer the part the resolution doesn't cover: you now have a class; where do *instances* come from — typed by hand per project, stored in a file, loaded from a list you maintain?

If Part 5 surfaced a new question, open OQ-5.

---

# What we're *not* doing yet

* No calculation functions
* No tests
* No persistence or file formats
* No validation logic
* No inheritance, base classes, or `EquipmentBase`
* No asking an agent to "design a data model for solar equipment"

That last one is the whole point. An agent asked cold will produce a plausible, generic, over-specified model in seconds. Yours will be smaller, stranger, and correct — because it came from a calculation you actually did.

---

# Challenge Questions

Six this time.

### 1. Derivation
Name one field that would almost certainly have appeared in an imagined-first data model, but is absent from yours. Why did nothing need it?

### 2. Units
Where did a unit conversion appear in your hand calculation? Where should it live in code — at input, at storage, at calculation, or at display? Defend the choice.

### 3. Property vs. assumption
You split the values into equipment properties and design assumptions. Give one value where the split was genuinely ambiguous, and explain what tipped it.

### 4. The boundary
You decided how close to the limit counts as a pass. State the rule and the reasoning. Then state what an agent would have chosen if you hadn't specified it, and what that would have cost.

### 5. Mutability
You made a call on `frozen=True`. Argue the opposing position as well as you can, then say whether it changed your mind.

### 6. Assumptions you invented
Part 3(c) required assumptions no document supplied. List them. For each: is it a domain decision, a research question, or something a competent programmer could pick? Anything in the first two categories belongs in the repository before the next mission.

---

## One rule for this mission

**The hand calculation is the specification.**

Not a warm-up for the specification — the specification itself. Every field in that dataclass should be traceable to a line in your work, and if you can't point to where you used something, it doesn't go in.

This is the discipline that makes delegation safe later. When you eventually hand an agent "implement the string sizing calculation," you'll be handing it a model with no spare parts and a worked example to check against. That's a very different act from asking it to figure out what solar equipment is.
