# Mission 1.3 — From Hand Calculation to Verified Code

You have a hand calculation in `/calcs/string_sizing.md` and a data model in `equipment.py`. This mission turns them into a program whose correctness is *checkable* rather than *assertable*.

That phrase is the whole mission. When you finish, you will not be able to say "the calculation works" — you'll be able to say "the calculation produces 42.12 V for these inputs, and here is the independent hand computation that also produces 42.12 V, and here is the test that fails if they ever diverge."

Two of your **pending** domain decisions will be forced closed by writing this code. That's not a coincidence. Decisions stay comfortable in the abstract and become unavoidable the moment something has to execute.

**Target time: 2 hours.** Every file path is specified.

---

## Mission objective

By the end:

1. Calculation functions in `calculations/string_sizing.py`
2. Tests in `tests/test_string_sizing.py` that check against your hand-computed values
3. A boundary test at 13 and 14 modules
4. Code limits living somewhere that isn't a literal buried in a function
5. Two domain decision rows closed
6. Everything committed

---

# Part 1 — Decide what a calculation returns

Before writing any function, close this pending row:

> A result is reported as pass/fail or as a number with margin

This is not a style question. Consider:

```python
check_max_string_voltage(module, inverter, count) -> bool
```

versus something that returns the computed voltage, the limit it was checked against, the margin, and whether it passed.

The first is easy to write and destroys information. When you later need to display the margin on a permit drawing, or warn that a design is at 99% of the limit, or explain to a plan reviewer *why* it passed, the boolean has already thrown that away and you'll be recomputing it somewhere else.

Write your decision into `docs/domain-decisions.md` with a reason. Then design a small result type in `calculations/results.py`:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class LimitCheck:
    """Result of checking a computed value against a limit."""
    value: float
    limit: float
    # what else does a reviewer need? add it.
```

Add whatever fields your decision implies. Consider at minimum: what the limit is *called*, what document it came from, and whether this was a pass. Note that `frozen=True` is right here for the same reason you argued in 1.2 — a result that can be mutated after the fact is not evidence of anything.

---

# Part 2 — Where limits live

Create `calculations/limits.py`.

The 600 V dwelling ceiling goes here, not inside a function. So does anything else that comes from a code document rather than a datasheet:

```python
# Values from published codes. Each entry cites its source.

# NEC 690.7(A), 2023 edition — maximum PV system voltage,
# one- and two-family dwellings
MAX_SYSTEM_VOLTAGE_DWELLING = 600.0  # V
```

Every constant carries a comment naming the document and edition. That's the auditability you described in your Q3 answer, in its simplest possible form — you can answer "what changes under the 2026 NEC?" by reading one file.

Do not build a jurisdiction lookup yet. One module with commented constants is the correct amount of structure for the number of constants you have.

---

# Part 3 — Write the calculations

Create `calculations/string_sizing.py`.

Four functions, mirroring your hand calc:

```python
def corrected_voc(module: PVModule, t_min: float) -> float:
    """Module Voc corrected to the design low temperature.

    Args:
        module: module parameters from the datasheet
        t_min: design low ambient temperature, °C

    Returns:
        Corrected open-circuit voltage, V

    Reference: calcs/string_sizing.md
    """
```

Then `corrected_vmp`, `max_modules_per_string`, and `min_modules_per_string`.

### Rules

**Pure functions.** No file reading, no printing, no input prompts, no database. Values in, values out. This is what makes them testable at all — a function that reads a file needs a file to exist before you can check its arithmetic.

**Rounding is explicit.** You specified round-down for max and round-up for min. Write that deliberately; do not let Python's default integer division decide it for you.

**Every docstring cites `calcs/string_sizing.md`.** When someone asks where a formula came from, the answer is in the code.

**Take the design temperature as a parameter**, not from a constant. It's site data, and your own three-bucket taxonomy says site data and universal constants live in different places.

---

# Part 4 — Tests from the hand calculation

Create `tests/test_string_sizing.py`.

Your hand calc has real numbers in it. Those are your test cases — not numbers you generate by running the code and pasting the output, which proves only that the code agrees with itself.

```python
def test_corrected_voc_matches_hand_calculation():
    """Verifies against calcs/string_sizing.md, Voc section."""
    module = PVModule(...)   # your real module
    result = corrected_voc(module, t_min=-29.1)
    assert result == pytest.approx(42.12, abs=0.01)
```

### The second pending decision

`pytest.approx` requires a tolerance, and choosing one closes this row:

> Numerical comparison tolerance in software code

Note what just happened. You split that row from engineering margin two missions ago, and here is the software one in isolation — it's about float representation and how many digits your hand calc carried, and it has nothing to do with whether the design is safe. The split was doing real work.

Write four tests, one per function, each citing the section of the hand calc it verifies.

---

# Part 5 — The boundary

Your hand calc says 13 modules. Test both sides:

```python
def test_thirteen_modules_within_inverter_limit():
    ...

def test_fourteen_modules_exceeds_inverter_limit():
    ...
```

A test that only checks the passing case tells you the function returns something. A test that checks both sides tells you the function *discriminates*, which is the only thing a limit check is for.

Add one more: a hypothetical inverter rated above 600 V, verifying that the dwelling ceiling governs instead of the equipment rating. That's the non-binding check from our last exchange, and this test is the reason it's worth having — the code path exists and is proven to work before anyone needs it.

Run everything:

```bash
pytest tests/ -v
```

---

# Part 6 — Verify, then commit

Before committing, do the thing that distinguishes this from ordinary software work.

Open `calcs/string_sizing.md` beside your test output. Confirm every number in the tests traces to a line in the hand calc. If a test contains a number that isn't in the hand calc, one of the two documents is wrong — find out which.

Then:

```bash
git add calculations/ tests/
git commit -m "Add string sizing calculations verified against hand calc"
```

Your Phase 1 definition of done says hand calculations are committed alongside the tests. This is the first time that's actually true.

---

# What we're *not* doing yet

* No CLI, no UI, no `input()`
* No JSON loading — instantiate equipment directly in the tests
* No validation of user input
* No error handling beyond what the calculations need
* No classes for anything that isn't data

And specifically: **do not ask an agent to write these four functions.** Not because it couldn't — because this is the mission where you find out whether you can read code well enough to check it. That capability is the 3 on your self-assessment, and it doesn't move by watching.

---

# Challenge Questions

### 1. Circular verification
Suppose you had written the functions first, run them, and pasted the output into the tests. The tests would pass. What exactly would they prove, and what would they fail to prove? Connect this to your Q6 answer from 1.1.

### 2. Purity
Why does `corrected_voc` take `t_min` as a parameter rather than reading it from a location database? Give a reason grounded in testing and a second reason grounded in your three-bucket taxonomy.

### 3. The result type
You chose what a limit check returns. Name one thing you can do with your chosen type that a bare `bool` would have made impossible, and be specific about where in the eventual application it matters.

### 4. Tolerance
State the tolerance you used and why. Then answer: if a test passes at `abs=0.01` but fails at `abs=0.001`, has the code found a bug, or has the test?

### 5. The unreachable branch
You wrote a test for the 600 V dwelling limit using an inverter you don't own. Argue against having written it. Then say why you'd keep it anyway — and note that this is the same question you asked me about the MPPT check, arriving at a different answer.

### 6. Reading code
Pick the function you're least confident about. Explain, line by line, what it does and why each line is there. If you reach a line you can't justify, that's the finding — say so rather than papering over it.

---

## One rule for this mission

**The hand calculation is the authority. The code is the implementation.**

If they disagree, the code is wrong until proven otherwise — and "proven otherwise" means finding the specific arithmetic error in the hand calc, not deciding the program is probably right because computers don't make mistakes.

This inverts the instinct most people develop with software, and it's the correct instinct for engineering software. The program is a device for applying a calculation you already trust to inputs you haven't tried yet. It is not a source of truth.
