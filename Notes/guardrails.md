# Standing rules to live by

## Guardrail #1
No AI may modify more code than I am willing to review line-by-line

## Guardrail #2
The 15-minute rule:

If I spend more than 15 minutes working on one error unsuccessfully:

1. Stop changing random things.
2. Read the error message completely.
3. Explain—in your own words—what you think it means.
4. Then ask the AI for help, including:
    - the full error message,
    - your code,
    - what you expected to happen,
    - what you've already tried.

## Guardrail #3
No unnecessary abstraction.

Without proper prompt guardrails, AI will attempt to "improve" the code with many changes.

The standing instruction to correct this type of behavior is:
    Solve the smallest problem that moves the project forward

## Guardrail #4
The more autonomy we give an agent, the stronger our automated verification needs to be.

As we increase agent autonomy, we're going to progressively move from:

Human writes code

toward:

Human specifies behavior
        ↓
Agent writes code
        ↓
Automated tests evaluate code
        ↓
Agent fixes failures
        ↓
Human reviews result

But we are not going to give an agent permission to autonomously modify a large project that has no tests. That's a recipe for token-burning and debugging nightmares.

## Guardrail #5
Use the simplest architecture that solves the current problem.