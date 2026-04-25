import { useState } from "react";
import { CreateOrderForm } from "./components/CreateOrderForm";
import { OrdersList } from "./components/OrdersList";
import { SystemLogs } from "./components/SystemLogs";
import { UploadPDF } from "./components/UploadPDF";
import { API_BASE_URL } from "./config";
import { Order, UploadResponse } from "./types";

function App() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [editingPatient, setEditingPatient] = useState<Order | null>(null);

  const addLog = (_message: string) => {};

  const handleExtract = (_data: UploadResponse) => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <main className="min-h-screen bg-slate-50 font-sans text-slate-900 antialiased">
      <div className="mx-auto max-w-7xl p-8">
      <header className="mb-6 rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Patient Management Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">Manage patient records and import from PDF.</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <aside className="space-y-6 rounded-xl border-r border-slate-200 bg-white p-5 lg:sticky lg:top-6 lg:self-start">
          <UploadPDF onExtract={handleExtract} onLog={addLog} />
          <CreateOrderForm
            editingPatient={editingPatient}
            onSaved={() => {
              setRefreshKey((prev) => prev + 1);
              setEditingPatient(null);
            }}
            onCancelEdit={() => setEditingPatient(null)}
            onLog={addLog}
          />

          <SystemLogs />
        </aside>

        <section className="flex-1">
          <OrdersList
            refreshKey={refreshKey}
            onEdit={(patientId) => {
              void (async () => {
                try {
                  const response = await fetch(`${API_BASE_URL}/orders/${patientId}`);
                  if (!response.ok) return;
                  const patient = (await response.json()) as Order;
                  setEditingPatient(patient);
                } catch {
                  // Keep UI minimal: ignore fetch errors here.
                }
              })();
            }}
            onLog={addLog}
          />
        </section>
      </div>
      </div>
    </main>
  );
}

export default App;
