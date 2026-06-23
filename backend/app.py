from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)


df_robots = pd.read_csv("../data/robots.csv")
df_telemetry = pd.read_csv("../data/telemetry.csv")
df_interactions = pd.read_csv("../data/interactions.csv")
df_vending = pd.read_csv("../data/vending.csv")
df_nav_events = pd.read_csv("../data/nav_events.csv")

if "state" in df_telemetry.columns:
    df_telemetry["state"] = df_telemetry["state"].str.lower()
if "zone" in df_telemetry.columns:
    df_telemetry["zone"] = df_telemetry["zone"].str.replace("_", "-", regex=False)

if "robot_id" in df_robots.columns:
    df_robots["robot_id"] = df_robots["robot_id"].astype(str).str.strip()


@app.route("/api/robots", methods=["GET"])
def get_robots():
    """
    Returns the fleet baseline overview, dynamically calculating Uptime Percentage
    strictly bounded between June 1, 2026 and June 14, 2026.
    """
    # 1. Parse dates for both telemetry and navigation events
    temp_telemetry = df_telemetry.copy()
    temp_nav = df_nav_events.copy()

    temp_telemetry["timestamp"] = pd.to_datetime(
        temp_telemetry["timestamp"], dayfirst=True, format="mixed", errors="coerce"
    )
    temp_nav["timestamp"] = pd.to_datetime(
        temp_nav["timestamp"], dayfirst=True, format="mixed", errors="coerce"
    )

    # 2. Apply strict June 1 to June 14 filter (using June 15 as the exclusive upper bound)
    start_date = pd.to_datetime("2026-06-01")
    end_date = pd.to_datetime("2026-06-15")

    temp_telemetry = temp_telemetry[
        (temp_telemetry["timestamp"] >= start_date)
        & (temp_telemetry["timestamp"] < end_date)
    ]
    temp_telemetry = temp_telemetry.dropna(subset=["timestamp"]).sort_values(
        by="timestamp"
    )

    temp_nav = temp_nav[
        (temp_nav["timestamp"] >= start_date) & (temp_nav["timestamp"] < end_date)
    ]

    # 3. Define fixed parameters for the exact 14-day window
    TOTAL_WINDOW_SECONDS = 14 * 24 * 60 * 60  # Exactly 14 days (1,209,600 seconds)
    GAP_THRESHOLD = pd.Timedelta(minutes=60)

    robots_payload = []
    raw_robots = df_robots.to_dict(orient="records")

    for robot in raw_robots:
        r_id = str(robot.get("robot_id")).strip()

        # --- A. Calculate Implicit Downtime (Offline > 60 mins) ---
        r_telemetry = temp_telemetry[
            temp_telemetry["robot_id"].astype(str).str.strip() == r_id
        ].copy()
        implicit_downtime_s = 0

        if not r_telemetry.empty:
            r_telemetry["time_diff"] = r_telemetry["timestamp"].diff()
            gaps = r_telemetry[r_telemetry["time_diff"] > GAP_THRESHOLD]
            implicit_downtime_s = gaps["time_diff"].dt.total_seconds().sum()
        else:
            implicit_downtime_s = TOTAL_WINDOW_SECONDS

        # --- B. Calculate Explicit Downtime (Critical Hardware Faults) ---
        r_nav_robot = temp_nav[temp_nav["robot_id"].astype(str).str.strip() == r_id]
        explicit_downtime_s = 0

        if not r_nav_robot.empty:
            critical_events = r_nav_robot[
                r_nav_robot["event_type"].isin(["fault", "estop", "manual_takeover"])
            ]
            explicit_downtime_s = (
                pd.to_numeric(critical_events["duration_s"], errors="coerce")
                .fillna(0)
                .sum()
            )

        # --- C. Final Uptime Math ---
        total_downtime_s = implicit_downtime_s + explicit_downtime_s
        actual_uptime_s = max(0, TOTAL_WINDOW_SECONDS - total_downtime_s)

        uptime_pct = round((actual_uptime_s / TOTAL_WINDOW_SECONDS) * 100, 1)

        robot["uptime_pct"] = uptime_pct

        if not r_telemetry.empty:
            robot["current_status"] = r_telemetry.iloc[-1]["state"]
        else:
            robot["current_status"] = "offline"

        robots_payload.append(robot)

    return jsonify(robots_payload)


@app.route("/api/robot/<robot_id>", methods=["GET"])
def get_robot_telemetry(robot_id):
    """Returns all telemetry data for a specific robot."""
    clean_id = str(robot_id).strip()

    robot_data = df_telemetry[
        df_telemetry["robot_id"].astype(str).str.strip() == clean_id
    ]

    if robot_data.empty:
        return jsonify({"error": f"No telemetry data found for robot {clean_id}"}), 404

    return jsonify(robot_data.to_dict(orient="records"))


@app.route("/api/robot/<robot_id>/event", methods=["GET"])
def get_robot_events(robot_id):
    """
    Returns a unified, chronological timeline of all events.
    Strictly flags errors based on predefined arrays for event_type, code,
    outcome, and payment_status.
    """
    clean_id = str(robot_id).strip()

    # 1. Base filter by robot_id
    interactions = df_interactions[
        df_interactions["robot_id"].astype(str).str.strip() == clean_id
    ].copy()
    vending = df_vending[
        df_vending["robot_id"].astype(str).str.strip() == clean_id
    ].copy()
    nav_events = df_nav_events[
        df_nav_events["robot_id"].astype(str).str.strip() == clean_id
    ].copy()
    telemetry = df_telemetry[
        df_telemetry["robot_id"].astype(str).str.strip() == clean_id
    ].copy()

    # 2. Tag Interactions (Strict Array: 'error', 'abandoned')
    interactions["event_category"] = "interaction"
    interactions["error"] = False
    interactions["errorColumn"] = None
    interactions["errorClass"] = None
    if not interactions.empty:
        err_mask = interactions["outcome"].isin(["error", "abandoned"])
        interactions.loc[err_mask, "error"] = True
        interactions.loc[err_mask, "errorColumn"] = "outcome"
        interactions.loc[err_mask, "errorClass"] = interactions.loc[err_mask, "outcome"]

    # 3. Tag Vending (Strict Array: 'failed', 'refunded')
    vending["event_category"] = "vending"
    vending["error"] = False
    vending["errorColumn"] = None
    vending["errorClass"] = None
    if not vending.empty:
        err_mask = vending["payment_status"].isin(["failed", "refunded"])
        vending.loc[err_mask, "error"] = True
        vending.loc[err_mask, "errorColumn"] = "payment_status"
        vending.loc[err_mask, "errorClass"] = vending.loc[err_mask, "payment_status"]

    # 4. Tag Navigation Events (Strict Arrays for type OR code)
    nav_events["event_category"] = "nav_event"
    nav_events["error"] = False
    nav_events["errorColumn"] = None
    nav_events["errorClass"] = None
    if not nav_events.empty:
        type_mask = nav_events["event_type"].isin(["fault", "estop", "manual_takeover"])
        code_mask = nav_events["code"].isin(
            ["SYS-500", "SAF-201", "OPS-301", "NAV-101"]
        )

        # Combine masks
        err_mask = type_mask | code_mask
        nav_events.loc[err_mask, "error"] = True

        # Determine which column triggered the flag
        nav_events.loc[type_mask, "errorColumn"] = "event_type"
        nav_events.loc[type_mask, "errorClass"] = nav_events.loc[
            type_mask, "event_type"
        ]

        # If it matches a specific code, let the code override as the primary error detail
        nav_events.loc[code_mask, "errorColumn"] = "code"
        nav_events.loc[code_mask, "errorClass"] = nav_events.loc[code_mask, "code"]

    # 5. Tag Telemetry (No errors flagged based on strict rules)
    telemetry["event_category"] = "telemetry"
    telemetry["error"] = False
    telemetry["errorColumn"] = None
    telemetry["errorClass"] = None

    # 6. Combine FIRST to prevent empty dataframe type collisions
    combined = pd.concat(
        [interactions, vending, nav_events, telemetry], ignore_index=True
    )

    if combined.empty:
        return jsonify([])

    # 7. Parse dates and sort chronologically
    combined["timestamp"] = pd.to_datetime(
        combined["timestamp"], dayfirst=True, format="mixed", errors="coerce"
    )
    combined = combined.dropna(subset=["timestamp"])

    if combined.empty:
        return jsonify([])

    combined = combined.sort_values(by="timestamp", ascending=True)
    combined["timestamp"] = combined["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Clean NaNs to None (null in JSON)
    combined = combined.where(pd.notnull(combined), None)
    raw_records = combined.to_dict(orient="records")
    formatted_timeline = []

    # 8. Restructure into the final JSON schema
    for record in raw_records:
        robot_id_val = record.pop("robot_id", None)
        event_cat_val = record.pop("event_category", None)
        timestamp_val = record.pop("timestamp", None)
        error_val = record.pop("error", False)

        error_col_val = record.pop("errorColumn", None)
        error_class_val = record.pop("errorClass", None)

        if isinstance(robot_id_val, str):
            robot_id_val = robot_id_val.strip()

        meta_data = {key: value for key, value in record.items() if value is not None}

        event_payload = {
            "robot_id": robot_id_val,
            "event_category": event_cat_val,
            "error": bool(error_val),
            "timestamp": timestamp_val,
            "meta": meta_data,
        }

        # Inject tracking keys only if an error occurred
        if error_val and error_col_val is not None:
            event_payload["errorColumn"] = error_col_val
            event_payload["errorClass"] = error_class_val

        formatted_timeline.append(event_payload)

    return jsonify(formatted_timeline)


@app.route("/api/robot/<robot_id>/anomally", methods=["GET"])
def get_robot_anomalies(robot_id):
    """
    Detects telemetry pings that occur immediately after a gap of >60 minutes.
    Scans the entire dataset (no date bounds) to ensure no ghost pings are missed.
    Returns the anomaly using a schema compatible with standard timeline events.
    """
    clean_id = str(robot_id).strip()

    # 1. Filter telemetry for the specific robot
    r_telemetry = df_telemetry[df_telemetry["robot_id"].astype(str).str.strip() == clean_id].copy()

    if r_telemetry.empty:
        return jsonify([])

    # 2. Parse dates natively
    r_telemetry["timestamp"] = pd.to_datetime(r_telemetry["timestamp"], dayfirst=True, format="mixed", errors="coerce")
    r_telemetry = r_telemetry.dropna(subset=["timestamp"])

    if r_telemetry.empty:
        return jsonify([])

    # 3. Sort chronologically
    r_telemetry = r_telemetry.sort_values(by="timestamp", ascending=True)

    # 4. Calculate time difference between consecutive pings
    r_telemetry["time_diff"] = r_telemetry["timestamp"].diff()

    # 5. Filter ONLY for the anomalous pings (gap > 60 minutes)
    anomalies = r_telemetry[r_telemetry["time_diff"] > pd.Timedelta(minutes=60)].copy()

    if anomalies.empty:
        return jsonify([])

    # 6. Format timestamps and clean NaNs
    anomalies["timestamp"] = anomalies["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    anomalies = anomalies.where(pd.notnull(anomalies), None)

    raw_records = anomalies.to_dict(orient="records")
    formatted_anomalies = []

    # 7. Restructure to match the required schema
    for record in raw_records:
        timestamp_val = record.pop("timestamp", None)
        robot_id_val = record.pop("robot_id", clean_id)
        
        # Remove the calculation column so it doesn't leak into the meta object
        record.pop("time_diff", None)
        
        if isinstance(robot_id_val, str):
            robot_id_val = robot_id_val.strip()
            
        meta_data = {key: value for key, value in record.items() if value is not None}
        
        formatted_anomalies.append({
            "timestamp": timestamp_val,
            "anomally": "timestamp", 
            "event_category": "telemetry",
            "robot_id": robot_id_val,
            "meta": meta_data
        })

    return jsonify(formatted_anomalies)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
