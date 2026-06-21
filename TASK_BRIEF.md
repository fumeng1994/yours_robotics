# Take-Home Exercise — Fleet Ops Console

**Role:** R&D Software Engineer, Yours Robotics (Singapore)
**Time budget:** ~3–5 hours. Please do not over-invest — prioritising well is part of the test.

---

## The scenario

You have joined the Singapore team. Our pilot fleet of interactive autonomous robots has
been operating for two weeks at Punggol Digital District (PDD). Each robot navigates the
site, runs interactions on its screens, handles QR scans and vending, and sits alongside
footfall sensors in each zone.

Operations has exported the raw logs and handed them to you. Right now, nobody on site can
see at a glance how the fleet is doing. **Your job: turn these raw exports into a simple
Fleet Ops Console that a non-engineer operator can open and understand.**

This is real-world field data. It was stitched together from several devices and vendors,
so treat it the way you would treat any production export — with healthy suspicion.

---

## What to build (core)

A small application with:

1. **A back end / API** that ingests the six CSV files in `data/` and computes operational
   metrics. (No database is required; reading the files is fine.)
2. **A lightweight front end** — a single dashboard is enough — that presents at least:
   - **Fleet overview:** how many robots, their current/last-known status, and which (if
     any) need attention.
   - **Per-robot drill-down:** select a robot and see its key numbers over the two weeks.
   - **A Data-Quality panel:** anything you found in the data that an operator or engineer
     should know about before trusting the numbers.
3. **Operational metrics**, including at least:
   - Per-robot **availability / uptime** over the window.
   - **Engagement:** interactions per robot (and per zone) per day.
   - **QR funnel:** scans → conversions, and the conversion rate.
   - **Vending revenue** per robot and per zone.
   - **Top fault / event types**.

> Some of these terms — for example "availability" or what counts as an "active" robot — we
> have deliberately **not** defined. Choose a sensible definition, **state it**, and explain
> why. We would rather see your judgment than a number that matches some hidden key.

## Stretch (optional — only if you have time and interest)

Pick what interests you; none of this is required:
- Automated anomaly detection / alerting rather than manual eyeballing.
- A clear commercial insight drawn from the data, with a recommended action.
- Tests, CI, Docker, a deployed link, basic auth, or a live-updating view.

We would rather see a focused, working core than a broad, broken one.

## R&D memo (≤ 1 page)

Add a short memo (`RND_MEMO.md`) proposing **one** new capability for our robots that you
believe is worth building. We will assess it primarily on **commercial viability**: be clear
about **who would pay for it and why** (a venue owner, a brand running a campaign, the
operator), sketch how you would build it, and say how you would validate it in the PDD pilot.

---

## What to submit

A link to a **Git repository** containing:

1. The application, with a `README.md` explaining how to run it from a clean clone.
2. **`DECISIONS.md`** — your assumptions, your metric definitions, the trade-offs you made,
   what you chose **not** to do and why, and known issues.
3. **`summary.json`** — a small machine-readable summary of your computed results (so we can
   check your numbers automatically). **Format below — please match the keys exactly.**
4. Your **commit history** (please commit as you work, not one final dump).
5. A **3–5 minute walkthrough** — a screen recording or a written `WALKTHROUGH.md`.

### `summary.json` format (required)

Place `summary.json` at the repository root. Use the values **after** your data cleaning.

```json
{
  "fleet": {
    "total_robots": 0,
    "active_robots": 0
  },
  "vending": {
    "total_revenue_sgd": 0.0,
    "transactions_counted": 0
  },
  "qr": {
    "total_scans": 0,
    "conversions": 0,
    "conversion_rate": 0.0
  },
  "metric_definitions": {
    "availability": "your one-line definition",
    "active_robots": "your one-line definition"
  },
  "data_quality": {
    "anomalies": [
      {
        "type": "short_label",
        "entity": "which robot/zone/file it affects",
        "note": "what's wrong and how you handled it"
      }
    ]
  }
}
```

The `data_quality.anomalies` list is important: it is how you tell us what you found in the
data. List one entry per distinct issue. Free-form `type` labels are fine.

---

## How we assess

Your submission is reviewed on five dimensions: **correctness & data handling**,
**engineering & code quality**, **product & commercial insight** (the memo), **communication**
(your DECISIONS.md and walkthrough), and **proactiveness & high agency** (how you handled the
ambiguity and what you chose to build). Part of the review is automated against your
`summary.json`; the rest, and the conversation in the second round, is where you explain your
reasoning.

A reminder, because it matters: **using AI is fine and encouraged.** What we are evaluating is
your judgment, your handling of imperfect real-world data, and your ability to explain and
defend the result. Build something you would be comfortable walking us through line by line.

Good luck — we are looking forward to it.
