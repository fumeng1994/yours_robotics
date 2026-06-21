# Data Dictionary — PDD Pilot Exports

Six CSV files in `data/`, covering roughly two weeks of operation (early June 2026) for the
Punggol Digital District pilot fleet. These are **raw exports** assembled from several
on-robot systems and third-party sensors. Fields are provided **as logged** — they have not
been cleaned, reconciled, or validated for you. Where a column's meaning or units are not
fully specified below, treat that as part of the exercise: decide on a reasonable
interpretation and record it.

A general note on timestamps: each value is recorded by its **source device or vendor**, and
those sources were not guaranteed to be configured identically. Do not assume every file —
or every robot — shares the same clock or timezone.

---

### `robots.csv` — the registered fleet
| Column | Meaning |
|---|---|
| `robot_id` | Unique robot identifier (e.g. `R-01`). |
| `model` | Hardware model. |
| `home_zone` | The PDD zone the robot is primarily assigned to. |
| `deploy_date` | Date the robot entered the pilot. |
| `firmware_version` | Firmware at export time. |

This is the authoritative list of robots that are *supposed* to be in the pilot.

### `telemetry.csv` — robot state samples
| Column | Meaning |
|---|---|
| `timestamp` | Sample time, as logged by the robot. |
| `robot_id` | Robot the sample belongs to. |
| `battery_pct` | Battery percentage at the sample. |
| `state` | Reported state (e.g. idle, navigating, interacting, charging). |
| `zone` | Zone the robot reported being in. |
| `x`, `y` | Position within the site (site-local coordinates). |
| `speed_mps` | Reported speed in metres/second. |

Sampled periodically through the day. The `state` field is what the robot *reported*; the
other fields describe what it was actually doing.

### `interactions.csv` — user engagement sessions
| Column | Meaning |
|---|---|
| `session_id` | Identifier for one interaction session. |
| `timestamp` | When the session occurred. |
| `robot_id` | Robot involved. |
| `type` | Interaction type: `qr_scan`, `screen_tap`, or `voice_chat`. |
| `campaign_id` | For QR scans, the campaign the scan was tied to (blank otherwise). |
| `duration_s` | Session length in seconds. |
| `outcome` | `completed`, `abandoned`, or `error`. |
| `converted` | For QR scans, whether the scan led to a conversion (`true`/`false`). |

A "conversion" means the QR scan led to a completed downstream action (e.g. an offer
claimed). How strictly you treat that is up to you.

### `vending.csv` — vending transactions
| Column | Meaning |
|---|---|
| `txn_id` | Transaction identifier. |
| `timestamp` | Transaction time. |
| `robot_id` | Robot that made the sale. |
| `sku` | Item sold. |
| `qty` | Quantity. |
| `amount` | Amount recorded by the on-robot payment module. |
| `payment_status` | `paid`, `failed`, or `refunded`. |

`amount` is recorded by each robot's payment module. Only `paid` transactions represent
realised revenue.

### `nav_events.csv` — navigation & operational events
| Column | Meaning |
|---|---|
| `timestamp` | Event time. |
| `robot_id` | Robot the event belongs to. |
| `event_type` | e.g. `path_blocked`, `replan`, `estop`, `manual_takeover`, `dock`, `undock`, `fault`. |
| `code` | Event/fault code. |
| `severity` | `info`, `warn`, or `error` (may be blank). |
| `duration_s` | How long the event lasted, in seconds. |

### `footfall.csv` — zone footfall counts
| Column | Meaning |
|---|---|
| `timestamp` | Hour of the count, as logged by the footfall sensor vendor. |
| `zone` | The PDD zone. |
| `count` | People counted in that zone that hour. |

Footfall is measured by a separate third-party sensor system, independent of the robots.

---

If something in the data looks wrong, it may well be — that is realistic. Use your judgment,
handle it sensibly, and tell us about it in your `DECISIONS.md` and `summary.json`.
