import { FormEvent, useEffect, useState } from "react";
import { Loader2, Save } from "lucide-react";
import { API_BASE_URL } from "../config";
import { CreateOrderRequest, Order, UpdateOrderRequest } from "../types";

interface CreateOrderFormProps {
  editingPatient: Order | null;
  onSaved: () => void;
  onCancelEdit: () => void;
  onLog: (message: string) => void;
}

const initialForm: CreateOrderRequest = {
  patient_first_name: "",
  patient_last_name: "",
  date_of_birth: "",
};

export function CreateOrderForm({
  editingPatient,
  onSaved,
  onCancelEdit,
  onLog,
}: CreateOrderFormProps) {
  const [form, setForm] = useState<CreateOrderRequest>(initialForm);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (editingPatient) {
      setForm({
        patient_first_name: editingPatient.patient_first_name,
        patient_last_name: editingPatient.patient_last_name,
        date_of_birth: editingPatient.date_of_birth,
      });
      setMessage(null);
      setError(null);
    }
  }, [editingPatient]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    setError(null);

    try {
      const endpoint = editingPatient
        ? `${API_BASE_URL}/orders/${editingPatient.id}`
        : `${API_BASE_URL}/orders`;
      const method = editingPatient ? "PUT" : "POST";
      const payload: CreateOrderRequest | UpdateOrderRequest = editingPatient
        ? ({ ...form } as UpdateOrderRequest)
        : form;

      const response = await fetch(endpoint, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        const detail = errorBody?.detail;

        if (Array.isArray(detail)) {
          const futureDobError = detail.find(
            (item: { loc?: unknown[]; msg?: string }) =>
              Array.isArray(item?.loc) &&
              item.loc.includes("date_of_birth") &&
              typeof item.msg === "string" &&
              item.msg.toLowerCase().includes("future")
          );
          if (futureDobError) {
            throw new Error("Date of birth cannot be in the future.");
          }
        }

        if (typeof detail === "string") {
          throw new Error(detail);
        }

        throw new Error(`${editingPatient ? "Save" : "Create"} failed (${response.status})`);
      }

      if (editingPatient) {
        setMessage("Patient record updated.");
        onLog(`Patient ${editingPatient.patient_first_name} ${editingPatient.patient_last_name} updated.`);
        onCancelEdit();
      } else {
        setMessage("Patient record created.");
        onLog(`Patient ${form.patient_first_name} ${form.patient_last_name} created.`);
      }
      setForm(initialForm);
      onSaved();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : `Failed to ${editingPatient ? "save" : "create"} patient record.`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-3">
      <h2 className="mb-4 text-lg font-semibold text-slate-900">
        {editingPatient ? "Edit Patient" : "Create Patient"}
      </h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        <label>
          <span className="mb-1 block text-sm font-medium text-slate-700">First Name</span>
          <input
            required
            className="w-full rounded-lg border border-slate-300 p-2 outline-none focus:ring-2 focus:ring-blue-500"
            value={form.patient_first_name}
            onChange={(e) => setForm((prev) => ({ ...prev, patient_first_name: e.target.value }))}
          />
        </label>
        <label>
          <span className="mb-1 block text-sm font-medium text-slate-700">Last Name</span>
          <input
            required
            className="w-full rounded-lg border border-slate-300 p-2 outline-none focus:ring-2 focus:ring-blue-500"
            value={form.patient_last_name}
            onChange={(e) => setForm((prev) => ({ ...prev, patient_last_name: e.target.value }))}
          />
        </label>
        <label>
          <span className="mb-1 block text-sm font-medium text-slate-700">Date of Birth</span>
          <input
            required
            type="date"
            className="w-full rounded-lg border border-slate-300 p-2 outline-none focus:ring-2 focus:ring-blue-500"
            value={form.date_of_birth}
            onChange={(e) => setForm((prev) => ({ ...prev, date_of_birth: e.target.value }))}
          />
        </label>
        <div className="flex gap-2 pt-1">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-all hover:bg-blue-700 disabled:opacity-70"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            {loading
              ? editingPatient
                ? "Saving..."
                : "Creating..."
              : editingPatient
                ? "Save Changes"
                : "Create Patient"}
          </button>
          {editingPatient && (
            <button
              type="button"
              onClick={onCancelEdit}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
          )}
        </div>
      </form>
      {message && <p className="mt-3 text-sm text-emerald-700">{message}</p>}
      {error && <p className="mt-3 text-sm text-rose-700">{error}</p>}
    </section>
  );
}
