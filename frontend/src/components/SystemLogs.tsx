import { useState } from "react";
import { API_BASE_URL } from "../config";

interface LogEntry {
  timestamp: string;
  action: "CREATE_ORDER" | "UPDATE_ORDER" | "DELETE_ORDER" | "UPLOAD_PDF" | string;
  entity_id: string;
  message: string;
}

export function SystemLogs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/logs`);
      if (!response.ok) {
        throw new Error("Failed to load logs");
      }
      const data = (await response.json()) as LogEntry[];
      setLogs(data);
    } catch {
      setError("Failed to load logs");
    } finally {
      setLoading(false);
    }
  };

  const formatEntityId = (entityId: string) => {
    if (!entityId) return "-";
    return entityId.length > 8 ? `${entityId.slice(0, 8)}...` : entityId;
  };

  const actionBadgeClass = (action: string) => {
    if (action.includes("CREATE")) {
      return "bg-emerald-100 text-emerald-700";
    }
    if (action.includes("DELETE")) {
      return "bg-rose-100 text-rose-700";
    }
    if (action.includes("EXTRACT") || action.includes("UPLOAD")) {
      return "bg-blue-100 text-blue-700";
    }
    return "bg-slate-100 text-slate-700";
  };

  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between p-5">
        <h2 className="text-lg font-semibold text-slate-900">System Logs</h2>
        <button
          onClick={() => void fetchLogs()}
          disabled={loading}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-all hover:bg-blue-700 disabled:opacity-70"
        >
          Refresh Logs
        </button>
      </div>

      {loading && <p className="px-5 pb-4 text-sm text-slate-500">Loading logs...</p>}
      {error && <p className="px-5 pb-4 text-sm text-rose-700">{error}</p>}

      {!loading && !error && logs.length === 0 && (
        <p className="px-5 pb-4 text-sm text-slate-500">No logs available.</p>
      )}

      {!loading && !error && logs.length > 0 && (
        <div className="max-h-[300px] overflow-y-auto">
          <table className="w-full text-left">
            <thead className="sticky top-0 bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Action</th>
                <th className="p-3">Entity ID</th>
                <th className="p-3">Message</th>
              </tr>
            </thead>
            <tbody className="text-sm text-slate-700">
              {logs.map((log, index) => (
                <tr key={`${log.timestamp}-${log.entity_id}-${index}`}>
                  <td className="border-t border-slate-100 p-3 font-mono text-xs">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="border-t border-slate-100 p-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold ${actionBadgeClass(log.action)}`}
                    >
                      {log.action}
                    </span>
                  </td>
                  <td className="border-t border-slate-100 p-3 font-mono text-xs" title={log.entity_id}>
                    {formatEntityId(log.entity_id)}
                  </td>
                  <td className="border-t border-slate-100 p-3 text-xs">{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
