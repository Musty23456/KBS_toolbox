import { useEffect, useState } from "react";
import { devicesApi } from "../../api/services";
import type { Device } from "../../api/types";

export function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  async function load() { setLoading(true); try { setDevices(await devicesApi.list()); } finally { setLoading(false); } }
  useEffect(() => { load(); }, []);
  return <div>
    <div className="page-header"><div><h1>Device Management</h1><p>Monitor field devices, sync health and app versions.</p></div><button onClick={load}>Refresh</button></div>
    {loading ? <p>Loading devices…</p> : <div className="table-wrap"><table><thead><tr><th>Device</th><th>User</th><th>App</th><th>Last seen</th><th>Last sync</th><th>Status</th><th>Failed</th><th>Actions</th></tr></thead><tbody>
      {devices.map(d => <tr key={d.id}><td>{d.device_id}</td><td>{d.user_id.slice(0,8)}</td><td>{d.app_version ?? "—"}</td><td>{d.last_seen_at ? new Date(d.last_seen_at).toLocaleString() : "Never"}</td><td>{d.last_sync_at ? new Date(d.last_sync_at).toLocaleString() : "Never"}</td><td>{d.is_active ? (d.last_sync_status ?? "ONLINE") : "INACTIVE"}</td><td>{d.failed_sync_count}</td><td><button onClick={async()=>{await devicesApi.requestSync(d.device_id); await load();}}>Request sync</button>{d.is_active && <button onClick={async()=>{await devicesApi.deactivate(d.device_id); await load();}}>Deactivate</button>}</td></tr>)}
    </tbody></table></div>}
  </div>;
}
