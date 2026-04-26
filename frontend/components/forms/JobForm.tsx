import { useState } from "react";
import { submitJob, uploadTranscript, getApiError } from "@/lib/api";
import { useJobPolling } from "@/hooks/useJobPolling";
import { Spinner } from "@/components/ui/Spinner";
import type { Quarter } from "@/types";

const QUARTERS: Quarter[] = ["Q1", "Q2", "Q3", "Q4"];
const CURRENT_YEAR = new Date().getFullYear();
const YEARS = Array.from({ length: 8 }, (_, i) => CURRENT_YEAR - i);

export function JobForm() {
  const [ticker, setTicker] = useState("");
  const [quarter, setQuarter] = useState<Quarter>("Q1");
  const [year, setYear] = useState(CURRENT_YEAR);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [transcriptText, setTranscriptText] = useState("");
  const [uploadingTranscript, setUploadingTranscript] = useState(false);

  const { status, jobData, isPolling } = useJobPolling(activeJobId);

  const validateTicker = (v: string): boolean => /^[A-Z]{1,5}$/.test(v);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const clean = ticker.trim().toUpperCase();
    if (!validateTicker(clean)) {
      setError("Ticker must be 1 to 5 uppercase letters, e.g. AAPL");
      return;
    }
    setSubmitting(true);
    try {
      const job = await submitJob(clean, quarter, year);
      setActiveJobId(job.id);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleTranscriptUpload = async () => {
    if (!activeJobId || !transcriptText.trim()) return;
    setUploadingTranscript(true);
    try {
      await uploadTranscript(activeJobId, transcriptText);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setUploadingTranscript(false);
    }
  };

  // Show transcript upload prompt
  if (status === "awaiting_upload") {
    return (
      <div className="card p-8 animate-in">
        <div className="flex items-start gap-3 mb-6">
          <div className="w-8 h-8 rounded-full bg-amber-50 border border-amber-200 flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M12 3a9 9 0 110 18A9 9 0 0112 3z" />
            </svg>
          </div>
          <div>
            <h3 className="font-semibold text-stone-900 mb-1">
              Transcript not found automatically
            </h3>
            <p className="text-sm text-stone-500">
              We could not fetch the transcript for{" "}
              <span className="font-mono font-medium text-stone-700">
                {jobData?.ticker} {jobData?.quarter} {jobData?.year}
              </span>{" "}
              from our data provider. Paste it below to continue.
            </p>
          </div>
        </div>
        <textarea
          value={transcriptText}
          onChange={(e) => setTranscriptText(e.target.value)}
          placeholder="Paste the full earnings call transcript here..."
          rows={10}
          className="input-base resize-none font-mono text-xs leading-relaxed mb-4"
        />
        {error && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2 mb-4">
            {error}
          </p>
        )}
        <button
          onClick={handleTranscriptUpload}
          disabled={!transcriptText.trim() || uploadingTranscript}
          className="btn-primary"
        >
          {uploadingTranscript ? <Spinner size="sm" /> : "Submit transcript"}
        </button>
      </div>
    );
  }

  // Show processing status
  if (activeJobId && status && status !== "failed") {
    return (
      <div className="card p-8 animate-in">
        <div className="flex items-center gap-4 mb-6">
          {isPolling && <Spinner size="md" />}
          <div>
            <p className="font-semibold text-stone-900">
              {status === "pending" && "Queuing analysis..."}
              {status === "processing" && "Pipeline running..."}
            </p>
            <p className="text-sm text-stone-500 mt-0.5">
              Analysing{" "}
              <span className="font-mono font-medium text-stone-700">
                {jobData?.ticker} {jobData?.quarter} {jobData?.year}
              </span>
            </p>
          </div>
        </div>

        <div className="space-y-2">
          {[
            "Fetching transcript",
            "Segmenting transcript",
            "Scoring sentiment",
            "Scoring confidence",
            "Extracting entities",
            "Generating summaries",
            "Verifying faithfulness",
          ].map((stage, i) => (
            <div key={stage} className="flex items-center gap-3">
              <div
                className={`w-1.5 h-1.5 rounded-full transition-colors duration-500 ${
                  status === "processing"
                    ? "bg-amber-400 animate-pulse-soft"
                    : "bg-stone-200"
                }`}
                style={{ animationDelay: `${i * 0.15}s` }}
              />
              <span className="text-sm text-stone-500">{stage}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Default: submission form
  return (
    <form onSubmit={handleSubmit} className="card p-8 animate-in">
      <h2 className="font-display text-xl font-semibold text-stone-900 mb-1">
        Analyse an earnings call
      </h2>
      <p className="text-stone-500 text-sm mb-7">
        Enter a ticker and quarter to run the full intelligence pipeline.
      </p>

      <div className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1.5">
            Ticker symbol
          </label>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="AAPL"
            maxLength={5}
            required
            className="input-base font-mono tracking-widest uppercase"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">
              Quarter
            </label>
            <select
              value={quarter}
              onChange={(e) => setQuarter(e.target.value as Quarter)}
              className="input-base"
            >
              {QUARTERS.map((q) => (
                <option key={q} value={q}>
                  {q}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">
              Year
            </label>
            <select
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="input-base"
            >
              {YEARS.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
            {error}
          </p>
        )}

        {status === "failed" && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
            {jobData?.error_message ?? "Analysis failed. Please try again."}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting || isPolling}
          className="btn-primary w-full"
        >
          {submitting ? <Spinner size="sm" /> : "Run analysis"}
        </button>
      </div>
    </form>
  );
}
