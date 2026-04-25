import { useEffect, useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { API_BASE_URL } from "../config";
import { Order } from "../types";

interface OrdersListProps {
  refreshKey: number;
  onEdit: (patientId: string) => void;
  onLog: (message: string) => void;
}

export function OrdersList({ refreshKey, onEdit, onLog }: OrdersListProps) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/orders`);
      if (!response.ok) {
        throw new Error(`Failed to fetch patient records (${response.status})`);
      }
      const data = (await response.json()) as Order[];
      setOrders(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load patient records.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchOrders();
  }, [refreshKey]);

  const handleDelete = async (id: string) => {
    const patient = orders.find((item) => item.id === id);
    const confirmed = window.confirm("Delete this patient record?");
    if (!confirmed) return;

    try {
      const response = await fetch(`${API_BASE_URL}/orders/${id}`, { method: "DELETE" });
      if (!response.ok) {
        throw new Error(`Delete failed (${response.status})`);
      }
      if (patient) {
        onLog(`Patient ${patient.patient_first_name} ${patient.patient_last_name} deleted.`);
      }
      await fetchOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed.");
    }
  };

  const formatPatientId = (id: string) => `PAT-${id.slice(0, 8).toUpperCase()}`;

  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="p-5">
      <h2 className="mb-4 text-lg font-semibold text-slate-900">Patient Directory</h2>
      {loading && <p className="mb-4 text-sm text-slate-500">Loading patient records...</p>}
      {error && <p className="mb-4 text-sm text-rose-700">{error}</p>}
      {!loading && orders.length === 0 && <p className="text-sm text-slate-500">No patient records yet.</p>}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
            <tr>
              <th className="p-4">Patient ID</th>
              <th className="p-4">Full Name</th>
              <th className="p-4">Date of Birth</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody className="text-sm text-slate-700">
            {orders.map((order) => (
              <tr key={order.id}>
                <td className="border-t border-slate-100 p-4 font-medium" title={order.id}>
                  {formatPatientId(order.id)}
                </td>
                <td className="border-t border-slate-100 p-4">{`${order.patient_first_name} ${order.patient_last_name}`}</td>
                <td className="border-t border-slate-100 p-4">{order.date_of_birth}</td>
                <td className="border-t border-slate-100 p-4">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onEdit(order.id)}
                      className="inline-flex items-center gap-1 rounded-md p-2 text-slate-600 hover:bg-slate-100"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => void handleDelete(order.id)}
                      className="inline-flex items-center gap-1 rounded-md p-2 text-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
