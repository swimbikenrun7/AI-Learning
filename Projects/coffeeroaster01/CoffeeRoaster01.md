# Coffee Roast Session Logger v0.1
We're deliberately keeping the scope tiny.

It will:

Ask a few questions
Perform one calculation
Print a nicely formatted summary

That's it.
No saving.
No files.
No AI.
No graphs.
No database.
Just one working program.

## Phase 1 - think
### Inputs - what information do we need?
Date
Machine name
Bean description
Green weight (g)
Finished weight (g)
Roast level

### Output - what do we want to display?
example:
August 1, 2026

Fresh Roast Session

Coffee: Ethiopia Sidama

Green Weight: 225 g
Finished Weight: 191 g

Weight Loss: 15.11%

### Tests

Should calculate_weight_loss_percentage(0,x) return anything?
    No.
    There needs to be an if statement to require user correction when green weight is entered as zero.

### Variable requirements

GREEN WEIGHT
- Must be numeric
- Must be > 0
- Must be < 500
- Otherwise ask again

FINISHED WEIGHT
- Must be numeric
- Must be > 0
- Must be < green weight
- Otherwise ask again

DATE
- Must be in the format MM-DD-YYYY (month - day - year)
- Otherwise ask again