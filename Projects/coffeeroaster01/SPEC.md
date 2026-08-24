# Coffee Roast Logger Specification

## Purpose

Record coffee roasting sessions and calculate basic roast metrics.

## Date
- must be in the format MM/DD/YYYY
- YYYY must be less than or equal to today()
- The program must continue requesting an input until the user provides a valid value.

## Green Weight

- Input must be numeric.
- Input must be greater than 100 and less than 300.
- Invalid input must produce a helpful error.
- User must be allowed to retry.

## Finished Weight

- Input must be numeric.
- Input must be greater than 100.
- Input must be less than green weight.
- Invalid input must produce a helpful error.
- User must be allowed to retry.

## Weight Loss

Weight loss percentage is calculated as:

(green weight - finished weight) / green weight × 100