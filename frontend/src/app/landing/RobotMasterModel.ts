export interface RobotMasterModel {
  deploy_date: string;
  firmware_version: string;
  home_zone: string;
  model: string;
  robot_id: string;
  uptime_pct: number;
  telemetry_anomally: boolean;
  total_revenue: number;
  total_interactions: number;
  converted_scans: number;
  total_scans: number;
}