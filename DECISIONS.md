<!-- # DECISIONS

> Replace each prompt below with your own reasoning. This document is one of the most
> important parts of your submission — it is where we see how you think. -->


## Metric definitions
<!-- - **Availability / uptime:** _how did you define it, and why?_
- **Active robot:** _what counts as active?_
- _Any other term you had to pin down..._ -->
- **Availability / uptime:**  Robot fail to ping after 2 consequetive 30mins, a robot that actively ping "OK" status is working well. Even if it is charging and not interacting, it is still consider operational and does not require attention.
- **Active robot:**   Robot that ping telemetry for that day / period and is a registered part of the fleet of 10 robots, any test robot should not be included in customer metric as test data might cause confusion.
- **Conversion Rate:**  Percentage of converted QR scan / Total QR Scan. Investigation of data show only QR Scan produce "true" conversions.
- **Total Revenue:** Calculated exclusively from vending transactions where payment_status is strictly `paid`. `failed` & `refunded` not added to total revenue.


## Assumptions I made
<!-- - _List the assumptions you made where the brief or data was ambiguous, and what you'd do
  differently if an assumption turned out to be wrong._ -->
- **Vending Missing Decimals:** I assumed that vending transaction amounts >= 100 (e.g., 600.0, 1800.0) were due to missing decimal points (i.e., representing $6.00 and $18.00). I implemented logic to automatically divide these anomalous values by 100 to prevent artificially inflated revenue metrics. I still flag it as an anomally, so even if assumption was wrong, it will still come to attention that there is an issue.
- **Telemetry Gaps:** I assumed a telemetry gap of >61 minutes represents a missed ping / offline status, provided it occurs after the initial boot sequence on June 1st. This assumption helped me to identify some strange timestamp outside of the testing window. 


## Data quality — what I found and how I handled it
<!-- - _One line per issue. (This should align with your `summary.json` anomalies.)_ -->
1) **Inconsistent Naming** (footfall.csv): Found underscores in zone names (e.g., PDD_A) and replaced '_' with '-' to standardize.
2) **Missing Data** (nav_events.csv): Found missing severity values and filled empty cells with 'unknown'.
3) **Inconsistent Capitalization** (telemetry.csv): Found mixed casing in robot states and converted all to lowercase using .str.lower().
4) **Formatting Anomalies** (telemetry.csv): Found underscores and trailing spaces in zones; replaced '_' with '-' and stripped spaces.
5) **Missing Decimal Point** (vending.csv): Found transaction amounts >= 100 (e.g., 350); assumed missing decimals and divided by 100.
6) **Out-of-Bounds Timestamps** (telemetry.csv): Found pre-deployment (May 30/31) and late sync (Jun 20) logs; filtered the dataset strictly to the June 1 - June 14 operational window.
7) **Unregistered Entities (R-99):** Found event logs for robots not listed in the main fleet registry. Handled by dynamically concatenating all `robot_id` columns across all CSVs during initialization and flagging the difference in the `summary.json` anomaly report.



## What I prioritised, and what I deliberately left out
<!-- - _What did you build first and why? What did you cut given the time budget?_ -->
What I did first:
1) **Actionable Error Flagging:** Highest priority is flagging errors (e.g., failed payments, missing decimals, NAV faults) as these usually require human attention.
2) **Business metrics:** Accurate revenue and conversion rates. End-goal of software product is still about making money.
3) **UI:** Friendliness and ease of use. Important for a management dashboard UI.

Deliberately left out
1) **Live updates:** I am unsure of input stream methods.
2) **Current/last-known status:** Static data provided is not effective to showcase this.
3) **Deployment instructions:** Too many options available, undecided until I know what is the full specification.



## Known issues / what I'd do with another day
<!-- - _Be honest. Self-awareness scores well._ -->
1) **Accuracy:** Check and test everything is working and data is absolutely correct across all edge cases.
2) **Automated test cases:** for the API endpoints.
3) **Data Completeness:** Did not use data from footfall.csv 
4) **Project Structure:** Project codebase should be modularise to ensure readability & maintainability
