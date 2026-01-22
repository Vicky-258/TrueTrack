"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import { api } from "@/lib/api";

/* ==============================
   Types
================================ */

type IntentChoice = {
  title: string;
  artists: string[];
  album?: string;
};

type MetadataChoice = {
  trackName: string;
  artistName: string;
  collectionName?: string;
  artworkUrl100?: string;
  _score?: number;
};

type InputRequired =
  | { type: "user_intent_selection"; choices: IntentChoice[] }
  | { type: "user_metadata_selection"; choices: MetadataChoice[] };

type JobResult = {
  success?: boolean;
  archived?: boolean;
  title?: string;
  artist?: string;
  album?: string;
  path?: string;
  reason?: string;
  error?: string;
};

type FinalMetadata = {
  trackName: string;
  artistName: string;
  collectionName?: string;
  artworkUrl100?: string;
};

type Job = {
  job_id: string;
  state: string;
  status: "running" | "waiting" | "success" | "error" | "cancelled";
  input_required?: InputRequired | null;
  final_metadata?: FinalMetadata | null;
  result?: JobResult | null;
  error?: { code: string; message: string } | null;
};

/* ==============================
   Page
================================ */

export default function JobPage() {
  const { id } = useParams<{ id: string }>();
  const jobId = id;

  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const isTerminal =
    job?.status === "success" ||
    job?.status === "error" ||
    job?.status === "cancelled";

  const fetchJob = useCallback(async () => {
    try {
      const data = await api<Job>(`/jobs/${jobId}`);
      setJob(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;
    fetchJob();
    if (isTerminal) return;
    const t = setInterval(fetchJob, 1500);
    return () => clearInterval(t);
  }, [jobId, fetchJob, isTerminal]);

  /* ==============================
     Guards
================================ */

  if (loading) return <div className="p-6">Loading job…</div>;
  if (error) return <div className="p-6 text-red-500">{error}</div>;
  if (!job) return <div className="p-6">Job not found</div>;

  const isWaiting = job.status === "waiting";
  const hasMetadata = Boolean(job.final_metadata);
  const result = job.result;
  const alreadyExists = result?.reason === "already_exists";

  /* ==============================
     Render
================================ */

  return (
    <main className="p-6 space-y-6">
      {/* Header */}
      <header className="space-y-1">
        <h1 className="text-xl font-semibold flex items-center gap-2">
          Job
          <span className="font-mono text-sm text-zinc-400">
            {job.job_id}
          </span>

          {job.status === "success" && (
            <span className="px-2 py-1 text-xs rounded bg-green-800 text-green-200">
              ✓ Completed
            </span>
          )}

          {job.status === "error" && (
            <span className="px-2 py-1 text-xs rounded bg-red-800 text-red-200">
              ✕ Failed
            </span>
          )}
        </h1>

        <p className="text-sm text-zinc-400">
          State: <b>{job.state}</b> · Status: <b>{job.status}</b>
        </p>
      </header>

      {/* Metadata Card */}
      {hasMetadata && job.final_metadata && (
        <section className="p-4 rounded bg-zinc-800 flex gap-4">
          {/* Album art */}
          {job.final_metadata.artworkUrl100 && (
            <Image
              src={job.final_metadata.artworkUrl100.replace(
                "100x100",
                "300x300"
              )}
              alt="Album art"
              width={128}
              height={128}
              className="rounded"
            />
          )}

          {/* Info */}
          <div className="flex-1 space-y-2">
            <div>
              <h2 className="text-lg font-semibold">
                {job.final_metadata.trackName}
              </h2>
              <p className="text-sm text-zinc-300">
                {job.final_metadata.artistName}
              </p>
              <p className="text-xs text-zinc-400">
                {job.final_metadata.collectionName}
              </p>
            </div>

            {/* Outcome */}
            {job.status === "success" && (
              <div
                className={`text-sm ${
                  alreadyExists ? "text-yellow-400" : "text-green-400"
                }`}
              >
                {alreadyExists
                  ? "♻ This track already existed. Reused existing file."
                  : "✓ Downloaded and saved successfully"}
              </div>
            )}

            {/* Path */}
            {job.status === "success" && result?.path && (
              <div className="text-xs text-zinc-400">
                Saved to:
                <div className="mt-1 font-mono bg-zinc-900 p-2 rounded">
                  {result.path}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* USER_INTENT_SELECTION */}
      {isWaiting &&
        job.input_required?.type === "user_intent_selection" && (
          <section className="space-y-3">
            <p className="text-yellow-300 font-semibold">
              Choose the correct track
            </p>

            {job.input_required.choices.map((c, i) => (
              <button
                key={i}
                className="w-full p-4 rounded bg-zinc-800 hover:bg-zinc-700 text-left"
                onClick={async () => {
                  await api(`/jobs/${jobId}/input`, {
                    method: "POST",
                    body: JSON.stringify({ choice: i }),
                  });
                  fetchJob();
                }}
              >
                <div className="font-semibold">{c.title}</div>
                <div className="text-sm text-zinc-400">
                  {c.artists.join(", ")} · {c.album ?? "Single"}
                </div>
              </button>
            ))}
          </section>
        )}

      {/* USER_METADATA_SELECTION */}
      {isWaiting &&
        job.input_required?.type === "user_metadata_selection" && (
          <section className="space-y-3">
            <p className="text-yellow-300 font-semibold">
              Select the correct metadata
            </p>

            {job.input_required.choices.map((m, i) => (
              <button
                key={i}
                className="w-full p-4 rounded bg-zinc-800 hover:bg-zinc-700 text-left"
                onClick={async () => {
                  await api(`/jobs/${jobId}/input`, {
                    method: "POST",
                    body: JSON.stringify({ choice: i }),
                  });
                  fetchJob();
                }}
              >
                <div className="font-semibold">
                  {m.trackName} — {m.artistName}
                </div>
                <div className="text-sm text-zinc-400">
                  {m.collectionName} · score{" "}
                  {m._score ? Math.round(m._score) : "?"}
                </div>
              </button>
            ))}
          </section>
        )}

      {/* Cancel */}
      {job.status === "running" && (
        <button
          className="px-4 py-2 rounded bg-red-700 hover:bg-red-600"
          onClick={async () => {
            await api(`/jobs/${jobId}/cancel`, { method: "POST" });
            fetchJob();
          }}
        >
          Cancel Job
        </button>
      )}

      {/* Raw JSON */}
      <details>
        <summary className="cursor-pointer text-sm text-zinc-400">
          Raw job JSON
        </summary>
        <pre className="mt-2 bg-zinc-900 p-4 rounded text-sm overflow-auto">
          {JSON.stringify(job, null, 2)}
        </pre>
      </details>
    </main>
  );
}
