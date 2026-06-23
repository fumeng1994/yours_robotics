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
    """Returns the fleet baseline overview."""
    return jsonify(df_robots.to_dict(orient="records"))


@app.route("/api/robot/<robot_id>", methods=["GET"])
def get_robot_telemetry(robot_id):
    """Returns all telemetry data for a specific robot."""
    clean_id = str(robot_id).strip()

    robot_data = df_telemetry[df_telemetry["robot_id"].astype(str).str.strip() == clean_id]
    
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
    interactions = df_interactions[df_interactions["robot_id"].astype(str).str.strip() == clean_id].copy()
    vending = df_vending[df_vending["robot_id"].astype(str).str.strip() == clean_id].copy()
    nav_events = df_nav_events[df_nav_events["robot_id"].astype(str).str.strip() == clean_id].copy()
    telemetry = df_telemetry[df_telemetry["robot_id"].astype(str).str.strip() == clean_id].copy()

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
        code_mask = nav_events["code"].isin(["SYS-500", "SAF-201", "OPS-301", "NAV-101"])
        
        # Combine masks
        err_mask = type_mask | code_mask
        nav_events.loc[err_mask, "error"] = True
        
        # Determine which column triggered the flag
        nav_events.loc[type_mask, "errorColumn"] = "event_type"
        nav_events.loc[type_mask, "errorClass"] = nav_events.loc[type_mask, "event_type"]
        
        # If it matches a specific code, let the code override as the primary error detail
        nav_events.loc[code_mask, "errorColumn"] = "code"
        nav_events.loc[code_mask, "errorClass"] = nav_events.loc[code_mask, "code"]

    # 5. Tag Telemetry (No errors flagged based on strict rules)
    telemetry["event_category"] = "telemetry"
    telemetry["error"] = False
    telemetry["errorColumn"] = None
    telemetry["errorClass"] = None

    # 6. Combine FIRST to prevent empty dataframe type collisions
    combined = pd.concat([interactions, vending, nav_events, telemetry], ignore_index=True)

    if combined.empty:
        return jsonify([])
    
    # 7. Parse dates and sort chronologically
    combined["timestamp"] = pd.to_datetime(combined["timestamp"], dayfirst=True, format="mixed", errors="coerce")
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
            "meta": meta_data
        }
        
        # Inject tracking keys only if an error occurred
        if error_val and error_col_val is not None:
            event_payload["errorColumn"] = error_col_val
            event_payload["errorClass"] = error_class_val
            
        formatted_timeline.append(event_payload)
        
    return jsonify(formatted_timeline)


if __name__ == "__main__":
    app.run(debug=True, port=5000)