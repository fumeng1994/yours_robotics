from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)


MEM_ROBOTS = []
MEM_TELEMETRY = {}
MEM_EVENTS = {}
MEM_ANOMALIES = {}

def init_memory():
    """
    Runs exactly once on server startup. Loads all CSVs, performs all
    Pandas calculations, sorts dates, and stores the final JSON-ready
    payloads into memory for instant retrieval by the API routes.
    """
    global MEM_ROBOTS, MEM_TELEMETRY, MEM_EVENTS, MEM_ANOMALIES
    print("Loading datasets and initializing memory cache...")

    df_robots = pd.read_csv("../data/robots.csv")
    df_telemetry = pd.read_csv("../data/telemetry.csv")
    df_interactions = pd.read_csv("../data/interactions.csv")
    df_vending = pd.read_csv("../data/vending.csv")
    df_nav_events = pd.read_csv("../data/nav_events.csv")

    # Global Data Cleaning 
    if "state" in df_telemetry.columns:
        df_telemetry["state"] = df_telemetry["state"].str.lower()
    if "zone" in df_telemetry.columns:
        df_telemetry["zone"] = df_telemetry["zone"].str.replace("_", "-", regex=False)

    for df in [df_robots, df_telemetry, df_interactions, df_vending, df_nav_events]:
        if "robot_id" in df.columns:
            df["robot_id"] = df["robot_id"].astype(str).str.strip()

    for df in [df_telemetry, df_interactions, df_vending, df_nav_events]:
        df["_dt"] = pd.to_datetime(df["timestamp"], dayfirst=True, format="mixed", errors="coerce")

    start_date = pd.to_datetime("2026-06-01")
    end_date = pd.to_datetime("2026-06-15")
    robot_ids = df_robots["robot_id"].unique()
    GAP_THRESHOLD = pd.Timedelta(minutes=61)


    # CACHE 1: Pre-calculate Anomalies Cache FIRST (Unbounded Dates)
    full_tel = df_telemetry.dropna(subset=["_dt"]).sort_values(by="_dt")

    DEPLOYMENT_DATE = pd.to_datetime("2026-06-01").date()

    for r_id in robot_ids:
        r_tel = full_tel[full_tel["robot_id"] == r_id].copy()
        anoms = []
        if not r_tel.empty:
            r_tel["time_diff"] = r_tel["_dt"].diff()
            gaps = r_tel[r_tel["time_diff"] > GAP_THRESHOLD].copy()
            
            if not gaps.empty:

                boot_limit = pd.to_datetime("2026-06-01 00:15:00")

                is_june_1st = (gaps["_dt"].dt.date == DEPLOYMENT_DATE)
                is_before_boot = (gaps["_dt"] <= boot_limit)

                gaps = gaps[~(is_june_1st & is_before_boot)]

                if not gaps.empty:
                    gaps["timestamp"] = gaps["_dt"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                    gaps = gaps.drop(columns=["_dt", "time_diff"])
                    gaps = gaps.where(pd.notnull(gaps), None)
                    
                    for rec in gaps.to_dict(orient="records"):
                        ts_val = rec.pop("timestamp", None)
                        rec.pop("robot_id", None)
                        meta = {k: v for k, v in rec.items() if v is not None}
                        anoms.append({
                            "timestamp": ts_val,
                            "anomally": "timestamp",
                            "event_category": "telemetry",
                            "robot_id": r_id,
                            "meta": meta
                        })
                    
        MEM_ANOMALIES[r_id] = anoms

    # CACHE 2: Pre-calculate Fleet Baseline (Uptime & Anomaly Flag)
    TOTAL_WINDOW_SECONDS = 14 * 24 * 60 * 60 
    
    up_tel = df_telemetry[(df_telemetry["_dt"] >= start_date) & (df_telemetry["_dt"] < end_date)].dropna(subset=["_dt"]).sort_values(by="_dt")
    up_nav = df_nav_events[(df_nav_events["_dt"] >= start_date) & (df_nav_events["_dt"] < end_date)]

    raw_robots = df_robots.to_dict(orient="records")
    for robot in raw_robots:
        r_id = robot["robot_id"]

        r_tel = up_tel[up_tel["robot_id"] == r_id].copy()
        if not r_tel.empty:
            r_tel["time_diff"] = r_tel["_dt"].diff()
            gaps = r_tel[r_tel["time_diff"] > GAP_THRESHOLD]
            implicit_downtime_s = gaps["time_diff"].dt.total_seconds().sum()
        else:
            implicit_downtime_s = TOTAL_WINDOW_SECONDS

        r_nav = up_nav[up_nav["robot_id"] == r_id]
        if not r_nav.empty:
            crit = r_nav[r_nav["event_type"].isin(["fault", "estop", "manual_takeover"])]
            explicit_downtime_s = pd.to_numeric(crit["duration_s"], errors="coerce").fillna(0).sum()
        else:
            explicit_downtime_s = 0

        total_downtime_s = implicit_downtime_s + explicit_downtime_s
        actual_uptime_s = max(0, TOTAL_WINDOW_SECONDS - total_downtime_s)
        robot["uptime_pct"] = round((actual_uptime_s / TOTAL_WINDOW_SECONDS) * 100, 1)

        robot["telemetry_anomally"] = len(MEM_ANOMALIES.get(r_id, [])) > 0

        if not r_tel.empty:
            robot["current_status"] = r_tel.iloc[-1]["state"]
        else:
            robot["current_status"] = "offline"

    MEM_ROBOTS.extend(raw_robots)

    # CACHE 3: Pre-calculate Telemetry Array
    for r_id in robot_ids:
        r_data = df_telemetry[df_telemetry["robot_id"] == r_id].drop(columns=["_dt"], errors="ignore")
        MEM_TELEMETRY[r_id] = r_data.where(pd.notnull(r_data), None).to_dict(orient="records")


    # CACHE 4: Pre-calculate Unified Events Timeline
    i_df = df_interactions.copy()
    i_df["event_category"] = "interaction"
    i_df["error"] = False; i_df["errorColumn"] = None; i_df["errorClass"] = None
    mask = i_df["outcome"].isin(["error", "abandoned"])
    i_df.loc[mask, "error"] = True
    i_df.loc[mask, "errorColumn"] = "outcome"
    i_df.loc[mask, "errorClass"] = i_df.loc[mask, "outcome"]

    v_df = df_vending.copy()
    v_df["event_category"] = "vending"
    v_df["error"] = False; v_df["errorColumn"] = None; v_df["errorClass"] = None
    mask = v_df["payment_status"].isin(["failed", "refunded"])
    v_df.loc[mask, "error"] = True
    v_df.loc[mask, "errorColumn"] = "payment_status"
    v_df.loc[mask, "errorClass"] = v_df.loc[mask, "payment_status"]

    n_df = df_nav_events.copy()
    n_df["event_category"] = "nav_event"
    n_df["error"] = False; n_df["errorColumn"] = None; n_df["errorClass"] = None
    t_mask = n_df["event_type"].isin(["fault", "estop", "manual_takeover"])
    c_mask = n_df["code"].isin(["SYS-500", "SAF-201", "OPS-301", "NAV-101"])
    n_df.loc[t_mask | c_mask, "error"] = True
    n_df.loc[t_mask, "errorColumn"] = "event_type"
    n_df.loc[t_mask, "errorClass"] = n_df.loc[t_mask, "event_type"]
    n_df.loc[c_mask, "errorColumn"] = "code"
    n_df.loc[c_mask, "errorClass"] = n_df.loc[c_mask, "code"]

    t_df = df_telemetry.copy()
    t_df["event_category"] = "telemetry"
    t_df["error"] = False; t_df["errorColumn"] = None; t_df["errorClass"] = None

    combined = pd.concat([i_df, v_df, n_df, t_df], ignore_index=True)
    combined = combined.dropna(subset=["_dt"])
    combined = combined[(combined["_dt"] >= start_date) & (combined["_dt"] < end_date)]
    combined = combined.sort_values(by="_dt", ascending=True)
    combined["timestamp"] = combined["_dt"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    combined = combined.drop(columns=["_dt"])
    combined = combined.where(pd.notnull(combined), None)

    for r_id in robot_ids:
        r_comb = combined[combined["robot_id"] == r_id]
        raw_events = r_comb.to_dict(orient="records")
        timeline = []
        for rec in raw_events:
            r_id_val = rec.pop("robot_id", None)
            cat_val = rec.pop("event_category", None)
            ts_val = rec.pop("timestamp", None)
            err_val = rec.pop("error", False)
            col_val = rec.pop("errorColumn", None)
            cls_val = rec.pop("errorClass", None)
            
            meta = {k: v for k, v in rec.items() if v is not None}
            payload = {
                "robot_id": r_id_val,
                "event_category": cat_val,
                "error": bool(err_val),
                "timestamp": ts_val,
                "meta": meta
            }
            if err_val and col_val is not None:
                payload["errorColumn"] = col_val
                payload["errorClass"] = cls_val
            timeline.append(payload)
            
        MEM_EVENTS[r_id] = timeline

    print("Memory cache initialized successfully! Server ready.")

init_memory()



# API 

@app.route("/api/robots", methods=["GET"])
def get_robots():
    """Returns the fleet baseline overview."""
    return jsonify(MEM_ROBOTS)

@app.route("/api/robot/<robot_id>", methods=["GET"])
def get_robot_telemetry(robot_id):
    """Returns all telemetry data for a specific robot."""
    clean_id = str(robot_id).strip()
    data = MEM_TELEMETRY.get(clean_id)
    if not data:
        return jsonify({"error": f"No telemetry data found for robot {clean_id}"}), 404
    return jsonify(data)

@app.route("/api/robot/<robot_id>/event", methods=["GET"])
def get_robot_events(robot_id):
    """Returns a unified, chronological timeline of all events."""
    clean_id = str(robot_id).strip()
    return jsonify(MEM_EVENTS.get(clean_id, []))

@app.route("/api/robot/<robot_id>/anomally", methods=["GET"])
def get_robot_anomalies(robot_id):
    """Returns detected telemetry ping anomalies."""
    clean_id = str(robot_id).strip()
    return jsonify(MEM_ANOMALIES.get(clean_id, []))


if __name__ == "__main__":
    app.run(debug=True, port=5000)