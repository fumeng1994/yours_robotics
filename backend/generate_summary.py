import pandas as pd
import json
import os


def generate_summary():
    # 1. Load the relevant CSV files
    # Assumes the CSV files are in the same directory as the script
    try:
        robots_df = pd.read_csv("../data/robots.csv")
        vending_df = pd.read_csv("../data/vending.csv")
        interactions_df = pd.read_csv("../data/interactions.csv")
        telemetry_df = pd.read_csv("../data/telemetry.csv")
        footfall_df = pd.read_csv("../data/footfall.csv")
        nav_events_df = pd.read_csv("../data/nav_events.csv")
    except FileNotFoundError as e:
        print(f"Error loading files: {e}. Make sure all CSVs are in the directory.")
        return

    # 2. Fleet Metrics
    # Total robots registered in the fleet
    total_robots = int(robots_df["robot_id"].nunique())
    # Active robots: robots that have sent at least one telemetry ping
    active_robots = int(telemetry_df["robot_id"].nunique())

    # 3. Data Quality & Vending Metrics
    anomalies = []

    # --- GLOBAL CLEANING (inspired by app.py) ---
    for df_name, df in [
        ("robots.csv", robots_df),
        ("telemetry.csv", telemetry_df),
        ("interactions.csv", interactions_df),
        ("vending.csv", vending_df),
        ("nav_events.csv", nav_events_df),
    ]:
        if "robot_id" in df.columns:
            # Check for trailing spaces to log anomaly, then clean
            if df["robot_id"].astype(str).str.contains(r"^\s|\s$").any():
                anomalies.append(
                    {
                        "type": "Whitespace in ID",
                        "entity": f"{df_name} (robot_id column)",
                        "note": "Found leading/trailing whitespaces in robot_ids. Handled using .str.strip().",
                    }
                )
            df["robot_id"] = df["robot_id"].astype(str).str.strip()

    # --- 1. FOOTFALL ANOMALIES ---
    if "zone" in footfall_df.columns:
        if footfall_df["zone"].str.contains("_").any():
            footfall_df["zone"] = footfall_df["zone"].str.replace("_", "-", regex=False)
            anomalies.append(
                {
                    "type": "Inconsistent Naming",
                    "entity": "footfall.csv (zone column)",
                    "note": "Found underscores in zone names (e.g., PDD_A). Replaced '_' with '-' to standardize.",
                }
            )

    # --- 2. NAV_EVENTS ANOMALIES ---
    if "severity" in nav_events_df.columns:
        if nav_events_df["severity"].isnull().any():
            nav_events_df["severity"] = nav_events_df["severity"].fillna("unknown")
            anomalies.append(
                {
                    "type": "Missing Data",
                    "entity": "nav_events.csv (severity column)",
                    "note": "Found missing severity values. Filled empty cells with 'unknown'.",
                }
            )

    # --- 3. TELEMETRY ANOMALIES ---
    if "state" in telemetry_df.columns:
        if telemetry_df["state"].str.contains(r"[A-Z]").any():
            telemetry_df["state"] = telemetry_df["state"].str.lower()
            anomalies.append(
                {
                    "type": "Inconsistent Capitalization",
                    "entity": "telemetry.csv (state column)",
                    "note": "Found mixed casing in robot states. Converted all to lowercase using .str.lower().",
                }
            )

    if "zone" in telemetry_df.columns:
        if (
            telemetry_df["zone"].str.contains("_").any()
            or telemetry_df["zone"].str.contains(r"\s$").any()
        ):
            telemetry_df["zone"] = (
                telemetry_df["zone"].str.replace("_", "-", regex=False).str.strip()
            )
            anomalies.append(
                {
                    "type": "Formatting Anomalies",
                    "entity": "telemetry.csv (zone column)",
                    "note": "Found underscores and trailing spaces in zones. Replaced '_' with '-' and stripped spaces.",
                }
            )

    if "battery_pct" in telemetry_df.columns:
        if telemetry_df["battery_pct"].isnull().any():
            telemetry_df["battery_pct"] = telemetry_df["battery_pct"].fillna(
                0
            )  # Or previous value
            anomalies.append(
                {
                    "type": "Missing Data",
                    "entity": "telemetry.csv (battery_pct column)",
                    "note": "Found missing battery percentages. Filled with 0.",
                }
            )

    # --- 4. VENDING ANOMALIES ---
    if "amount" in vending_df.columns:
        high_amount_mask = vending_df["amount"] >= 100
        if high_amount_mask.any():
            vending_df.loc[high_amount_mask, "amount"] = (
                vending_df.loc[high_amount_mask, "amount"] / 100
            )
            anomalies.append(
                {
                    "type": "Missing Decimal Point",
                    "entity": "vending.csv (amount column)",
                    "note": "Found transaction amounts >= 100 (e.g., 350). Assumed missing decimals and divided by 100.",
                }
            )

    # --- 5. OUT-OF-BOUNDS DATE ANOMALIES (NEW) ---
    # Convert timestamps to datetime to check boundaries
    telemetry_df["_dt"] = pd.to_datetime(
        telemetry_df["timestamp"], dayfirst=True, format="mixed", errors="coerce"
    )

    start_date = pd.to_datetime("2026-06-01")
    end_date = pd.to_datetime("2026-06-15")  # Exclusive boundary for 14-day window

    # Check for out of bounds
    out_of_bounds = telemetry_df[
        (telemetry_df["_dt"] < start_date) | (telemetry_df["_dt"] >= end_date)
    ]
    if not out_of_bounds.empty:
        # Filter the dataset to only include the core window
        telemetry_df = telemetry_df[
            (telemetry_df["_dt"] >= start_date) & (telemetry_df["_dt"] < end_date)
        ]

        anomalies.append(
            {
                "type": "Out-of-Bounds Timestamps",
                "entity": "telemetry.csv",
                "note": "Found pre-deployment (May 30/31) and late sync (Jun 20) logs breaking the 30-min cadence. Filtered dataset strictly to June 1 - June 14.",
            }
        )

    # --- METRICS CALCULATION ---
    # Fleet Metrics
    total_robots = int(robots_df["robot_id"].nunique())
    active_robots = int(telemetry_df["robot_id"].nunique())

    # Vending Metrics
    paid_transactions = vending_df[vending_df["payment_status"].str.lower() == "paid"]
    total_revenue = float(paid_transactions["amount"].sum())
    transactions_counted = int(len(paid_transactions))

    # QR Metrics
    qr_interactions = interactions_df[interactions_df["type"] == "qr_scan"]
    total_scans = int(len(qr_interactions))
    conversions = int(
        len(
            qr_interactions[
                qr_interactions["converted"].astype(str).str.upper() == "TRUE"
            ]
        )
    )
    conversion_rate = float(conversions / total_scans) if total_scans > 0 else 0.0

    # Build the JSON structure strictly matching the provided template
    summary_data = {
        "fleet": {"total_robots": total_robots, "active_robots": active_robots},
        "vending": {
            "total_revenue_sgd": round(total_revenue, 2),
            "transactions_counted": transactions_counted,
        },
        "qr": {
            "total_scans": total_scans,
            "conversions": conversions,
            "conversion_rate": round(conversion_rate, 4),
        },
        "metric_definitions": {
            "availability": "Percentage of total operational time spent in non-fault and non-charging states.",
            "active_robots": "Any robot that has recorded at least one location/status ping in the telemetry dataset during the recording period.",
        },
        "data_quality": {
            "anomalies": anomalies
            if anomalies
            else [
                {
                    "type": "None",
                    "entity": "All files",
                    "note": "No obvious data anomalies were detected during the aggregation phase.",
                }
            ]
        },
    }

    # Export to JSON file
    output_filename = "summary.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print(
        f"Success: '{output_filename}' has been generated with {len(anomalies)} anomalies logged."
    )


if __name__ == "__main__":
    generate_summary()
