from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# 1. Load Data into Memory
df_robots = pd.read_csv('../data/robots.csv')
df_telemetry = pd.read_csv('../data/telemetry.csv')
df_interactions = pd.read_csv('../data/interactions.csv')
df_vending = pd.read_csv('../data/vending.csv')

# 2. Pre-process and Clean Telemetry Data (Run once on startup)
# Normalize the state strings to lowercase (fixes 'NAVIGATING' vs 'navigating')
if 'state' in df_telemetry.columns:
    df_telemetry['state'] = df_telemetry['state'].str.lower()

# Normalize zone strings to use dashes instead of underscores (fixes 'PDD_A' vs 'PDD-A')
if 'zone' in df_telemetry.columns:
    df_telemetry['zone'] = df_telemetry['zone'].str.replace('_', '-', regex=False)

# --- Routes ---

@app.route('/api/robots', methods=['GET'])
def get_robots():
    """Returns the fleet baseline overview."""
    return jsonify(df_robots.to_dict(orient='records'))

@app.route('/api/robot/<robot_id>', methods=['GET'])
def get_robot_telemetry(robot_id):
    """
    Returns all telemetry data for a specific robot.
    Example usage: GET /api/robot/R-10
    """
    # Filter the telemetry dataframe for the requested robot_id
    robot_data = df_telemetry[df_telemetry['robot_id'] == robot_id]
    
    # Handle the case where the robot ID doesn't exist or has no data
    if robot_data.empty:
        return jsonify({"error": f"No telemetry data found for robot {robot_id}"}), 404
        
    # Convert the filtered data to a JSON-friendly list of dictionaries
    payload = robot_data.to_dict(orient='records')
    
    return jsonify(payload)

@app.route('/api/robot/<robot_id>/event', methods=['GET'])
def get_robot_events(robot_id):
    """
    Returns a unified, chronological timeline of interactions and vending events.
    """
    # 1. Filter both datasets for the requested robot
    interactions = df_interactions[df_interactions['robot_id'] == robot_id].copy()
    vending = df_vending[df_vending['robot_id'] == robot_id].copy()
    
    # 2. Tag the data so the Angular frontend can differentiate the event types
    interactions['event_category'] = 'interaction'
    vending['event_category'] = 'vending'
    
    # 3. Concatenate the two DataFrames into one list
    combined = pd.concat([interactions, vending], ignore_index=True)
    
    # Handle the edge case where a robot has exactly zero events
    if combined.empty:
        return jsonify([])
        
    # 4. Sort chronologically (Earliest to Latest)
    # Convert string timestamps to actual datetime objects to ensure perfect sorting
    combined['timestamp'] = pd.to_datetime(combined['timestamp'])
    combined = combined.sort_values(by='timestamp', ascending=True)
    
    # Convert datetime back to a standard ISO string for clean JSON serialization
    combined['timestamp'] = combined['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # 5. Clean up the data for JSON
    # When combining different schemas, Pandas fills missing columns with NaN. 
    # We must convert NaN to None so it renders as `null` in JSON rather than breaking.
    combined = combined.where(pd.notnull(combined), None)
    
    return jsonify(combined.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)