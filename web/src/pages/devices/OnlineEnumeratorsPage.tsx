import { useCallback, useEffect, useMemo, useState } from "react";
import { apiClient } from "../../api/client";

type PresenceStatus = "ONLINE" | "AWAY" | "OFFLINE";

interface EnumeratorPresence {
  user_id: string;
  full_name: string;
  email: string;
  device_id: string | null;
  app_version: string | null;
  last_seen_at: string | null;
  last_sync_at: string | null;
  last_sync_status: string | null;
  seconds_since_seen: number | null;
  status: PresenceStatus;
}

interface PresenceResponse {
  server_time: string;
  counts: { online: number; away: number; offline: number; total: number };
  enumerators: EnumeratorPresence[];
}

const REFRESH_MS = 15000;

function timeAgo(iso: string | null, now: number): string {
  if (!iso) return "Never";
  const seconds = Math.max(0, Math.floor((now - new Date(iso).getTime()) / 1000));
  if (seconds < 10) return "Just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days > 1 ? "s" : ""} ago`;
}

function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function OnlineEnumeratorsPage() {
  const [data, setData] = useState<PresenceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"ALL" | PresenceStatus>("ALL");
  const [search, setSearch] = useState("");
  const [now, setNow] = useState(Date.now());
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);

  const load = useCallback(async () => {
    try {
      const response = await apiClient.get<PresenceResponse>("/api/devices/online-enumerators");
      setData(response.data);
      setError(null);
      setLastRefreshed(new Date());
    } catch {
      setError("Could not load enumerator status. Retrying automatically…");
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-refresh from the server every 15 seconds
  useEffect(() => {
    load();
    const interval = setInterval(load, REFRESH_MS);
    return () => clearInterval(interval);
  }, [load]);

  // Keep the "x min ago" labels ticking between refreshes
  useEffect(() => {
    const tick = setInterval(() => setNow(Date.now()), 20000);
    return () => clearInterval(tick);
  }, []);

  const visible = useMemo(() => {
    if (!data) return [];
    const q = search.trim().toLowerCase();
    return data.enumerators.filter((e) => {
      if (filter !== "ALL" && e.status !== filter) return false;
      if (!q) return true;
      return e.full_name.toLowerCase().includes(q) || e.email.toLowerCase().includes(q);
    });
  }, [data, filter, search]);

  const counts = data?.counts ?? { online: 0, away: 0, offline: 0, total: 0 };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Online enumerators</h1>
          <p>See who is active in the field right now. Updates automatically every 15 seconds.</p>
        </div>
        <div className="live-indicator">
          <span className="presence-dot presence-online" />
          <span>Live{lastRefreshed ? ` · ${lastRefreshed.toLocaleTimeString()}` : ""}</span>
          <button className="btn btn-secondary" onClick={load}>
            Refresh
          </button>
        </div>
      </div>

      {error && <p className="form-error">{error}</p>}

      <div className="stat-row">
        <button
          type="button"
          className={`stat-box stat-filter ${filter === "ONLINE" ? "is-selected" : ""}`}
          onClick={() => setFilter(filter === "ONLINE" ? "ALL" : "ONLINE")}
        >
          <div className="stat-value stat-online">{counts.online}</div>
          <div className="stat-label">Online now</div>
        </button>
        <button
          type="button"
          className={`stat-box stat-filter ${filter === "AWAY" ? "is-selected" : ""}`}
          onClick={() => setFilter(filter === "AWAY" ? "ALL" : "AWAY")}
        >
          <div className="stat-value stat-away">{counts.away}</div>
          <div className="stat-label">Recently active</div>
        </button>
        <button
          type="button"
          className={`stat-box stat-filter ${filter === "OFFLINE" ? "is-selected" : ""}`}
          onClick={() => setFilter(filter === "OFFLINE" ? "ALL" : "OFFLINE")}
        >
          <div className="stat-value stat-offline">{counts.offline}</div>
          <div className="stat-label">Offline</div>
        </button>
        <button
          type="button"
          className={`stat-box stat-filter ${filter === "ALL" ? "is-selected" : ""}`}
          onClick={() => setFilter("ALL")}
        >
          <div className="stat-value">{counts.total}</div>
          <div className="stat-label">Total enumerators</div>
        </button>
      </div>

      <div className="toolbar">
        <input
          type="search"
          placeholder="Search by name or email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading ? (
        <p className="loading-text">Loading…</p>
      ) : visible.length === 0 ? (
        <div className="empty-state">
          <h3>No enumerators to show</h3>
          <p>
            {counts.total === 0
              ? "No active enumerator accounts yet."
              : "Nobody matches this filter right now."}
          </p>
        </div>
      ) : (
        <div className="presence-grid">
          {visible.map((e, index) => (
            <div
              key={e.user_id}
              className={`presence-card presence-card-${e.status.toLowerCase()}`}
              style={{ animationDelay: `${Math.min(index, 12) * 40}ms` }}
            >
              <div className="presence-avatar">
                {initials(e.full_name)}
                <span className={`presence-dot presence-${e.status.toLowerCase()} presence-avatar-dot`} />
              </div>
              <div className="presence-body">
                <div className="presence-name">{e.full_name}</div>
                <div className="presence-email">{e.email}</div>
                <div className="presence-meta">
                  <span className={`presence-pill presence-pill-${e.status.toLowerCase()}`}>
                    {e.status === "ONLINE" ? "Online" : e.status === "AWAY" ? "Recently active" : "Offline"}
                  </span>
                  <span>Last seen: {timeAgo(e.last_seen_at, now)}</span>
                </div>
                <div className="presence-meta presence-meta-soft">
                  <span>Last sync: {timeAgo(e.last_sync_at, now)}</span>
                  {e.app_version && <span>v{e.app_version}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
