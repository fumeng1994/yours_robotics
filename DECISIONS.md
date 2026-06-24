# DECISIONS

> Replace each prompt below with your own reasoning. This document is one of the most
> important parts of your submission — it is where we see how you think.

## Metric definitions
- **Availability / uptime:** _how did you define it, and why?_ robot fail to ping after 2 consequetive 30mins
- **Active robot:** _what counts as active?_  robot that ping telemetry for that day
- _Any other term you had to pin down..._

## Assumptions I made
- _List the assumptions you made where the brief or data was ambiguous, and what you'd do
  differently if an assumption turned out to be wrong._

## Data quality — what I found and how I handled it
- _One line per issue. (This should align with your `summary.json` anomalies.)_

1) dates before 1jun and 14jun - intentionally omitted because it does tally with my assumption for consequtive pings
2) 


## What I prioritised, and what I deliberately left out
- _What did you build first and why? What did you cut given the time budget?_
1) highest priority is flagging errors, usually require human attention so tackled 1st
2) business metric, revenue, conversation rate
3) bugs, anomally, outliers
4) UI friendlines and ease of use

Deliberately left out
1) Live updates - I am unsure of input stream methods
2) Test case - better to get more data before doing consolidated
3) Deployment instruction - many options available, undecided until I know what is the full specification


## Known issues / what I'd do with another day
- _Be honest. Self-awareness scores well._

1) check and test everything is working and data is correct
2) build test cases
