from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# --- 1. Data Ingestion ---
# Note: Paths assume you are running this from a directory alongside the data folder (e.g., src/)
df_robots = pd.read_csv("../data/robots.csv")
df_telemetry = pd.read_csv("../data/telemetry.csv")
df_interactions = pd.read_csv("../data/interactions.csv")
df_vending = pd.read_csv("../data/vending.csv")
df_nav_events = pd.read_csv("../data/nav_events.csv")

# --- 2. Global Data Cleaning ---
# Normalize text casing and string formatting anomalies
if "state" in df_telemetry.columns:
    df_telemetry["state"] = df_telemetry["state"].str.lower()
if "zone" in df_telemetry.columns:
    df_telemetry["zone"] = df_telemetry["zone"].str.replace("_", "-", regex=False)

# Strip hidden whitespace from master robot registry
if "robot_id" in df_robots.columns:
    df_robots["robot_id"] = df_robots["robot_id"].astype(str).str.strip()


# --- 3. API Routes ---

@app.route("/api/robots", methods=["GET"])
def get_robots():
    """Returns the fleet baseline overview."""
    return jsonify(df_robots.to_dict(orient="records"))


@app.route("/api/robot/<robot_id>", methods=["GET"])
def get_robot_telemetry(robot_id):
    """Returns all telemetry data for a specific robot."""
    clean_id = str(robot_id).strip()
    
    # Strip whitespace during comparison to avoid false negatives
    robot_data = df_telemetry[df_telemetry["robot_id"].astype(str).str.strip() == clean_id]
    
    if robot_data.empty:
        return jsonify({"error": f"No telemetry data found for robot {clean_id}"}), 404
        
    return jsonify(robot_data.to_dict(orient="records"))


@app.route("/api/robot/<robot_id>/event", methods=["GET"])
def get_robot_events(robot_id):
    """
    Returns a unified, chronological timeline of interactions, vending, 
    nav_events, and telemetry.
    """
    clean_id = str(robot_id).strip()

    # 1. Filter standard datasets (stripping whitespace)
    interactions = df_interactions[df_interactions["robot_id"].astype(str).str.strip() == clean_id].copy()
    vending = df_vending[df_vending["robot_id"].astype(str).str.strip() == clean_id].copy()
    nav_events = df_nav_events[df_nav_events["robot_id"].astype(str).str.strip() == clean_id].copy()
    telemetry = df_telemetry[df_telemetry["robot_id"].astype(str).str.strip() == clean_id].copy()
    
    # 2. Tag categories
    interactions["event_category"] = "interaction"
    vending["event_category"] = "vending"
    nav_events["event_category"] = "nav_event"
    telemetry["event_category"] = "telemetry"
        
    # 3. Safely Parse Mixed-Format Dates BEFORE combining
    if not interactions.empty:
        interactions["timestamp"] = pd.to_datetime(interactions["timestamp"], format="mixed", errors="coerce")
    if not vending.empty:
        vending["timestamp"] = pd.to_datetime(vending["timestamp"], format="mixed", errors="coerce")
    if not nav_events.empty:
        nav_events["timestamp"] = pd.to_datetime(nav_events["timestamp"], format="mixed", errors="coerce")
    if not telemetry.empty:
        telemetry["timestamp"] = pd.to_datetime(telemetry["timestamp"], format="mixed", errors="coerce")
    
    # 4. Combine into a single DataFrame
    combined = pd.concat([interactions, vending, nav_events, telemetry], ignore_index=True)
    
    if combined.empty:
        return jsonify([])
        
    # 5. Sort chronologically
    combined = combined.dropna(subset=["timestamp"]) 
    combined = combined.sort_values(by="timestamp", ascending=True)
    combined["timestamp"] = combined["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Convert NaNs to None for clean JSON handling
    combined = combined.where(pd.notnull(combined), None)
    
    # 6. Restructure into the target 'meta' JSON schema
    raw_records = combined.to_dict(orient="records")
    formatted_timeline = []
    
    for record in raw_records:
        robot_id_val = record.pop("robot_id", None)
        event_cat_val = record.pop("event_category", None)
        timestamp_val = record.pop("timestamp", None)
        
        if isinstance(robot_id_val, str):
            robot_id_val = robot_id_val.strip()
            
        meta_data = {key: value for key, value in record.items() if value is not None}
        
        formatted_timeline.append({
            "robot_id": robot_id_val,
            "event_category": event_cat_val,
            "timestamp": timestamp_val,
            "meta": meta_data
        })
        
    return jsonify(formatted_timeline)


if __name__ == "__main__":
    app.run(debug=True, port=5000)