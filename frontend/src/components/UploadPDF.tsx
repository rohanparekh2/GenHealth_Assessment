import { FormEvent, useState } from "react";
import { Loader2, Upload } from "lucide-react";
import { API_BASE_URL } from "../config";
import { UploadResponse } from "../types";

interface UploadPDFProps {
  onExtract: (data: UploadResponse) => void;
  onLog: (message: string) => void;
}

export function UploadPDF({ onExtract, onLog }: UploadPDFProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<UploadResponse | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) {
      setError("Please choose a PDF file.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        const message =
          typeof errorBody?.detail === "string"
            ? errorBody.detail
            : `Upload failed (${response.status})`;
        throw new Error(message);
      }

      const data = (await response.json()) as UploadResponse;
      setResult(data);
      onExtract(data);
      onLog("PDF extracted successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      onLog("PDF extraction failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-3">
      <h2 className="mb-4 text-lg font-semibold text-slate-900">Quick Import</h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="file"
          accept="application/pdf"
          className="w-full rounded-lg border border-slate-300 p-2 outline-none focus:ring-2 focus:ring-blue-500"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-all hover:bg-blue-700 disabled:opacity-70"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
          {loading ? "Extracting..." : "Extract from PDF"}
        </button>
      </form>

      {error && <p className="mt-3 text-sm text-rose-700">{error}</p>}

      {result && (
        <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
          <p>
            <strong>First Name:</strong> {result.first_name ?? "Not found"}
          </p>
          <p>
            <strong>Last Name:</strong> {result.last_name ?? "Not found"}
          </p>
          <p>
            <strong>Date of Birth:</strong> {result.date_of_birth ?? "Not found"}
          </p>
        </div>
      )}
    </section>
  );
}
