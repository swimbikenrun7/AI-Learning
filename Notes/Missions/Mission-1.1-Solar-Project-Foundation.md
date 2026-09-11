# Mission 1.1 — Project Foundation: Vision, Scope, and Decomposition

This is the first mission of the numbered curriculum. The 0.x series is closed.

Everything up to 0.14.4 existed to make you dangerous with tools: a shell, Python, Git, tests, static analysis, a GUI framework, and a coding agent. Those were foundations. You now have all of them, and the last of them — agentic AI — has been evaluated honestly rather than accepted on faith.

Mission 1 starts the real work: **the solar application.**

This mission contains no code. That is deliberate, and it is not a warm-up.

The most common failure mode in software projects is not bad code. It is a project that never established what it was supposed to do, discovered that fact 4,000 lines in, and had to be abandoned or rebuilt. You already know this from structural work — nobody starts detailing connections before the lateral system is defined. Software teams do it constantly anyway.

You are also about to hand parts of this project to an AI agent. An agent will happily generate 500 lines against a vague goal. The document you write in this mission is the thing that makes delegated work *checkable*.

---

## Mission objective

By the end of this mission you should have:

1. A real repository for the solar application, initialized and committed.
2. A README that a competent stranger could read and understand what this project is, what it is not, and where it is going.
3. An explicit scope boundary, including what is deliberately excluded.
4. A phase decomposition with a definition of "done" for each phase.
5. A documented separation between **domain decisions** (yours) and **implementation decisions** (delegable).
6. A chosen first calculation, with acceptance criteria written before any code exists.

And you should understand the difference between:

```text
vision        — why this exists
scope         — what is and is not included
requirements  — what must be true
architecture  — how it is structured
implementation— how it is coded
```

These get collapsed into each other constantly. Keeping them separate is most of the discipline.

**Target time: 2 hours.** Size limits are given throughout. Respect them. A specification nobody reads is worse than no specification, because it creates the illusion of one.

---

# Part 1 — Repository decision

Before creating anything, make a decision and write down why.

The solar application could live:

* **(a)** as a subdirectory inside `AI-Learning`
* **(b)** as its own repository

Consider at minimum:

* Does the solar application have a different lifetime than the curriculum?
* Might it eventually be published, shared, or sold?
* Does its Git history benefit from being separate from coffee-logger commits?
* Would a collaborator ever need one without the other?
* Is `AI-Learning` a *portfolio of exercises* or a *product repository*?

Write your decision and a two-to-three sentence justification. Keep it — it goes in the README later.

Then create the repository and make an initial commit. Empty-ish is fine:

```bash
mkdir -p ~/src/<your-project-name>
cd ~/src/<your-project-name>
git init
printf '# <Project Name>\n\nProject foundation in progress.\n' > README.md
git add README.md
git commit -m "Initial commit: project skeleton"
```

Adapt paths to your machine. Naming the project is your call — but pick something you can live with typing for two years, and avoid naming it after a technology you might replace.

---

# Part 2 — The vision statement

Write **one paragraph, 100 words maximum**, answering:

> What does this application do, for whom, and why is that worth doing?

### Constraints

The vision statement may **not** contain any of the following:

* a programming language
* a framework or library
* a file format
* a database
* a user-interface technology
* the words "using AI"

If you cannot describe the value of the application without naming a technology, you do not yet understand the application. This is the single most useful test in the mission.

### A worked example from a different domain

Bad:

> A Python application using SQLite and a Textual GUI that stores coffee roast records and calculates weight loss percentages.

Better:

> A record-keeping tool for home coffee roasters that captures each roast's inputs and outcomes so the roaster can identify which conditions produced good coffee and reproduce them deliberately rather than by memory.

Notice the second one tells you *why anyone would want it*. The first tells you what it is made of. Only the second can tell you whether a proposed feature belongs.

---

# Part 3 — Scope boundaries

Produce three lists. **No more than 8 items each.**

```text
IN SCOPE           — the application is not complete without this
OUT OF SCOPE       — deliberately excluded, possibly forever
DEFERRED           — will likely be included, but not now
```

The distinction between OUT OF SCOPE and DEFERRED matters more than it looks. "Out of scope" means a future request for it gets declined. "Deferred" means it gets scheduled. Conflating them is how projects grow without anyone deciding to grow them.

### Deliberately provocative candidates

Assign each of these to one of the three lists. You may not skip any:

* Battery/storage system design
* Ground-mount systems
* Structural attachment and roof-load verification
* Utility interconnection application forms
* Shading analysis
* Multiple jurisdictions' amendments to the electrical code
* Cost estimation and financial payback
* Users outside the United States
* Users who are not the homeowner (installers, AHJs)
* Any code year other than the one you choose to target

That last one is not a trick. Decide now which code edition the application targets, and write it down. You are a PE; you already know why this is the kind of assumption that quietly poisons a calculation library if it is left implicit.

---

# Part 4 — The domain boundary

This is the part that will matter most when you delegate work.

Produce a two-column table. **Minimum 6 rows per column.**

| Only I can decide this | A competent programmer could decide this |
| ---------------------- | ---------------------------------------- |

Left column: things where getting it wrong is an *engineering* error — a wrong answer, an unsafe design, a rejected permit. Right column: things where getting it wrong is a *software* error — annoying, refactorable, non-fatal.

Some genuinely ambiguous cases to force you to think:

* Rounding behavior on a voltage calculation
* Whether temperatures are stored in °C or °F internally
* Whether a value is stored or recalculated on demand
* Default values offered to the user
* What happens when a required input is missing
* The tolerance used when comparing two floating-point results
* Units displayed to the user vs. units used internally

At least three of those belong in the left column, and the reasoning is not the same for each. Justify anything you find genuinely ambiguous in one sentence.

This table is the thing you will paste into an agent prompt for the next two years. Take it seriously.

---

# Part 5 — Phase decomposition

Break the application into **no more than 6 phases**.

For each phase, give:

```text
Name
One-sentence purpose
Definition of done  (how you will know it is finished)
What it depends on
```

### Rules

1. Phase 1 must be small enough to actually finish.
2. Every phase must produce something *verifiable*, not merely something *written*.
3. "Definition of done" may not be "it works." State how you would demonstrate it.
4. No phase may depend on a later phase.

The roadmap you inherited suggested a progression roughly like: foundation → domain model → calculations → verification → external data → configuration → UI → diagrams → permit output. That is a reasonable starting point, and you are free to disagree with it. If you do disagree, say why. An inherited roadmap is a hypothesis, not a requirement.

---

# Part 6 — Specification structure

Decide where durable project knowledge will live, and create the skeleton.

A defensible starting structure:

```text
README.md                  the why/what/where
docs/
  scope.md                 Part 3 output
  domain-decisions.md      Part 4 output, and every future domain ruling
  roadmap.md               Part 5 output
specs/
  <one file per calculation or component>
```

Create the directories and files. They may be nearly empty. What matters is that a location exists, so that the next time you make a decision there is an obvious place to put it — decisions that have no home end up in a chat transcript, and chat transcripts are not project memory.

### The rule that makes this work

> If a decision needs to be re-explained to an agent more than once, it belongs in the repository, not in the conversation.

Write that rule into `README.md`. You will violate it repeatedly anyway; having it written down shortens the recovery time.

---

# Part 7 — Write the README and commit

Assemble the README. **Target 400–600 words. Hard ceiling 800.**

Suggested sections:

```text
Project name
Vision            (Part 2)
Status            (honest: "foundation; no implementation yet")
Scope summary     (short — link to docs/scope.md for the full lists)
Target code edition and jurisdiction assumptions
Roadmap summary   (link to docs/roadmap.md)
Who decides what  (link to docs/domain-decisions.md)
How this project is developed  (your workflow: spec → agent → verify → diff → human commit)
```

Then commit — as a human, with a real message:

```bash
git add .
git commit -m "Establish project foundation: vision, scope, roadmap, domain boundary"
git log --stat
```

Read the `git log --stat` output. Confirm that what you committed is what you think you committed. This habit is cheap now and valuable later.

---

# Part 8 — Nominate the first calculation

The next mission builds actual code. This part chooses the target.

Propose **three candidate calculations** that could be the application's first implemented piece of engineering logic. For each, state:

* the inputs
* the output
* how you would verify the answer is correct *without running the program*

Then pick one and defend the choice.

### What makes a good first calculation

```text
few inputs
single unambiguous output
you can compute it by hand
a wrong answer is obviously wrong
it is genuinely needed by the real application
it does not require external data sources
```

### What makes a bad first calculation

```text
requires weather or irradiance data
requires a lookup table you don't have yet
produces a result only a simulation could confirm
has legitimate professional disagreement about method
"annual energy production"
```

Annual energy production is the one everybody wants to build first and it is close to the worst possible starting point — you cannot hand-verify it, it depends on external datasets, and a subtly wrong answer looks completely plausible. Notice how many of the "bad" criteria it hits at once.

Maximum string voltage under cold-temperature conditions is the kind of thing that scores well on the "good" list — bounded inputs, hand-checkable, and wrong answers are unsafe rather than merely inaccurate. Whether that is *your* first calculation, and what the correct method and code basis actually are, is your call. I can help you implement and verify a calculation; I cannot be the authority on whether it is engineering-correct. That boundary is permanent and it is the whole reason Part 4 exists.

---

# What we're *not* doing yet

Do **not**, in this mission:

* write application code
* choose a web framework
* choose a GUI framework
* choose a database
* choose a diagram/rendering library
* design a data schema
* set up packaging, virtual environments, or dependencies
* ask an agent to "scaffold the project"

That last one is the real temptation. A frontier agent will produce a plausible project skeleton in thirty seconds. It will also silently make a dozen architectural decisions on your behalf, and you will inherit all of them without ever having considered the alternatives.

The scaffolding is not the hard part. The decisions are.

---

# Challenge Questions

Answer these in one response when the assignments are complete.

### 1. Vision
Your vision statement was constrained to exclude all technology. What did that constraint force you to notice that you would otherwise have skipped?

### 2. Scope
Pick one item you placed in OUT OF SCOPE. Describe a plausible future situation in which you would be tempted to move it to DEFERRED. What would have to be true for that to be the right decision rather than scope creep?

### 3. The code-edition assumption
You committed to a target code edition. Where in the application will that assumption physically live, and what would it cost you if it were spread across forty calculation functions as literal numbers instead?

### 4. Domain boundary
You assigned floating-point comparison tolerance to one of the two columns. Defend that placement. Then argue the opposite position as well as you can.

### 5. Decomposition
Why does the rule "no phase may depend on a later phase" matter more for an AI-assisted project than for one you write entirely yourself?

### 6. Definition of done
Compare these two definitions of done for a calculation phase:

```text
A: "The string voltage calculation is implemented and the tests pass."
B: "For five documented input cases spanning the expected range, the
    program's output matches an independently hand-computed value."
```

Both sound rigorous. Explain precisely what B protects you from that A does not — and connect this to something you already learned in the 0.x series.

### 7. Context
This mission produced documents rather than code. Explain how those documents change what you have to type into an agent prompt six months from now, and why that is worth two hours today.

### 8. The scaffolding temptation
Suppose you had opened with: *"Set up a Python project for a residential solar design application."* List at least four decisions the agent would have made for you. For each, state whether you would have noticed.

### 9. Transfer
Structural engineering has an equivalent of this mission — the work done before any member is sized. Name the equivalent, and identify one place where the analogy **breaks down**. The failure of the analogy is the interesting part.

### 10. Honest assessment
Rate your current confidence, and be candid rather than generous:

| Item | Confidence (1–5) |
| ---- | ---------------- |
| I know what this application is for | ? |
| I know what it will not do | ? |
| I know what the first working version contains | ? |
| I could hand Phase 1 to an agent and check its work | ? |
| I could explain this project to another engineer in five minutes | ? |

Any score of 3 or below tells us where Mission 1.2 needs to spend its time. Under-report rather than over-report — an inflated score costs you a mission spent in the wrong place.

---

## One additional rule for this mission

**Write the specification you would want to receive, not the one you would want to write.**

You have been on the receiving end of vague structural criteria from an architect or owner. You know exactly what it costs downstream. The document you are producing here is the same instrument, pointed at your future self and at every agent you delegate to.

The test is simple: hand the README to someone who has never heard of this project, and see whether they can tell you what the first version does.

If they cannot, the specification is not finished — no matter how long it is.
