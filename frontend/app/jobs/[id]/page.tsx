"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Music2,
  User2,
  Disc,
  Clock,
  Terminal,
  Play,
  PauseCircle
} from "lucide-react";

/* ==============================
   Types
================ ================ */

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
  can_resume?: boolean;
};

/* ==============================
   Page
================ ================ */

export default function JobPage() {
  const { id } = useParams<{ id: string }>();
  const jobId = id;

  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showLogs, setShowLogs] = useState(false);

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
    const t = setInterval(fetchJob, 1000);
    return () => clearInterval(t);
  }, [jobId, fetchJob, isTerminal]);

  /* ==============================
     Guards
  ================ ================ */

  if (loading) return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
      <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
      <p className="text-muted-foreground animate-pulse">Loading job context...</p>
    </div>
  );

  if (error) return (
    <div className="p-6 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 flex items-center gap-3">
      <AlertCircle size={24} />
      <div>
        <h3 className="font-semibold">Error Loading Job</h3>
        <p className="text-sm opacity-90">{error}</p>
      </div>
    </div>
  );

  if (!job) return <div className="p-6">Job not found</div>;

  const isWaiting = job.status === "waiting";
  const hasMetadata = Boolean(job.final_metadata);
  const result = job.result;
  const alreadyExists = result?.reason === "already_exists";

  /* ==============================
     Render
  ================ ================ */

  return (
    <main className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800 pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">Job Details</h1>
            <StatusBadge status={job.status} />
          </div>
          <p className="text-sm font-mono text-zinc-500 flex items-center gap-2">
            <span className="select-all">{job.job_id}</span>
            •
            <span className="text-zinc-400">{job.state}</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          {job.can_resume && (
            <button
              onClick={async () => {
                await api(`/jobs/${jobId}/resume`, { method: "POST" });
                fetchJob();
              }}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-500 transition-colors text-sm font-medium"
            >
              <Play size={16} /> Resume Job
            </button>
          )}

          {job.status === "running" && (
            <button
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-colors text-sm font-medium border border-red-500/20"
              onClick={async () => {
                await api(`/jobs/${jobId}/cancel`, { method: "POST" });
                fetchJob();
              }}
            >
              <PauseCircle size={16} /> Cancel
            </button>
          )}
        </div>
      </header>

      {/* Error Banner */}
      {job.status === "error" && job.error && (
        <div className="p-4 rounded-xl bg-red-950/30 border border-red-500/30 text-red-200">
          <h3 className="font-semibold flex items-center gap-2 mb-1 text-red-400">
            <XCircle size={18} />
            Pipeline Failed
          </h3>
          <p className="text-sm font-mono opacity-80 pl-6">
            {job.error.message || "Unknown error occurred"}
          </p>
        </div>
      )}

      {/* Metadata Card */}
      {hasMetadata && job.final_metadata && (
        <section className="relative overflow-hidden p-6 rounded-2xl bg-zinc-900 border border-zinc-800/50 flex flex-col sm:flex-row gap-6">
          {/* Background Glow */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl -z-10" />

          {/* Album art */}
          <div className="shrink-0 relative group">
            {job.final_metadata.artworkUrl100 ? (
              <Image
                src={job.final_metadata.artworkUrl100.replace(
                  "100x100",
                  "600x600"
                )}
                alt="Album art"
                width={160}
                height={160}
                className="rounded-xl shadow-2xl group-hover:scale-105 transition-transform duration-500"
              />
            ) : (
              <div className="w-40 h-40 rounded-xl bg-zinc-800 flex items-center justify-center text-zinc-600">
                <Music2 size={40} />
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 space-y-4">
            <div className="space-y-1">
              <h2 className="text-2xl font-bold leading-tight">
                {job.final_metadata.trackName}
              </h2>
              <div className="flex items-center gap-2 text-lg text-zinc-300">
                <User2 size={18} className="text-zinc-500" />
                {job.final_metadata.artistName}
              </div>
              <div className="flex items-center gap-2 text-sm text-zinc-500">
                <Disc size={16} />
                {job.final_metadata.collectionName}
              </div>
            </div>

            {/* Outcome */}
            {job.status === "success" && (
              <div className={cn(
                "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium border",
                alreadyExists
                  ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                  : "bg-green-500/10 text-green-500 border-green-500/20"
              )}>
                {alreadyExists ? (
                  <>
                    <AlertCircle size={14} />
                    Track already exists
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={14} />
                    Download complete
                  </>
                )}
              </div>
            )}

            {/* Path */}
            {job.status === "success" && result?.path && (
              <div className="pt-2">
                <div className="text-xs text-zinc-500 uppercase tracking-wider font-semibold mb-1.5">Saved Location</div>
                <code className="text-xs bg-black/30 px-3 py-2 rounded-lg text-zinc-400 font-mono block w-full overflow-x-auto">
                  {result.path}
                </code>
              </div>
            )}
          </div>
        </section>
      )}

      {/* USER_INTENT_SELECTION */}
      {isWaiting &&
        job.input_required?.type === "user_intent_selection" && (
          <section className="space-y-4 animate-in fade-in slide-in-from-bottom-2">
            <div className="flex items-center gap-2 text-yellow-500">
              <AlertCircle size={20} />
              <h3 className="font-semibold">Multiple Matches Found</h3>
            </div>

            <p className="text-sm text-zinc-400">
              Turn off "Interactive Mode" to auto-select the best match in the future.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {job.input_required.choices.map((c, i) => (
                <button
                  key={i}
                  className="p-4 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-blue-500/50 hover:bg-zinc-800/80 text-left transition-all group"
                  onClick={async () => {
                    await api(`/jobs/${jobId}/input`, {
                      method: "POST",
                      body: JSON.stringify({ choice: i }),
                    });
                    fetchJob();
                  }}
                >
                  <div className="font-semibold group-hover:text-blue-400 transition-colors">{c.title}</div>
                  <div className="text-sm text-zinc-400 mt-1">
                    {c.artists.join(", ")}
                  </div>
                  {c.album && (
                    <div className="text-xs text-zinc-500 mt-2 flex items-center gap-1">
                      <Disc size={12} /> {c.album}
                    </div>
                  )}
                </button>
              ))}
            </div>
          </section>
        )}

      {/* USER_METADATA_SELECTION */}
      {isWaiting &&
        job.input_required?.type === "user_metadata_selection" && (
          <section className="space-y-4 animate-in fade-in slide-in-from-bottom-2">
            <div className="flex items-center gap-2 text-yellow-500">
              <AlertCircle size={20} />
              <h3 className="font-semibold">Select Metadata</h3>
            </div>

            <div className="space-y-2">
              {job.input_required.choices.map((m, i) => (
                <button
                  key={i}
                  className="w-full flex items-center gap-4 p-4 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-blue-500/50 hover:bg-zinc-800/80 text-left transition-all group"
                  onClick={async () => {
                    await api(`/jobs/${jobId}/input`, {
                      method: "POST",
                      body: JSON.stringify({ choice: i }),
                    });
                    fetchJob();
                  }}
                >
                  {m.artworkUrl100 ? (
                    <Image
                      src={m.artworkUrl100}
                      alt=""
                      width={48}
                      height={48}
                      className="rounded bg-zinc-800"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded bg-zinc-800 flex items-center justify-center">
                      <Music2 size={20} className="text-zinc-600" />
                    </div>
                  )}

                  <div className="flex-1 min-w-0">
                    <div className="font-semibold truncate group-hover:text-blue-400 transition-colors">
                      {m.trackName}
                    </div>
                    <div className="text-sm text-zinc-400 truncate">
                      {m.artistName} • {m.collectionName}
                    </div>
                  </div>

                  <div className="text-xs font-mono text-zinc-500 bg-zinc-950 px-2 py-1 rounded">
                    {m._score ? Math.round(m._score) : "?"}%
                  </div>
                </button>
              ))}
            </div>
          </section>
        )}

      {/* Debug Info */}
      <div className="pt-8 border-t border-zinc-800">
        <button
          onClick={() => setShowLogs(!showLogs)}
          className="flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          <Terminal size={12} />
          {showLogs ? "Hide Debug Data" : "Show Debug Data"}
        </button>

        {showLogs && (
          <pre className="mt-4 bg-black/50 p-4 rounded-xl text-xs font-mono text-zinc-500 overflow-auto max-h-96 border border-zinc-800">
            {JSON.stringify(job, null, 2)}
          </pre>
        )}
      </div>
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles = {
    running: "bg-blue-500/10 text-blue-500 border-blue-500/20",
    waiting: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
    success: "bg-green-500/10 text-green-500 border-green-500/20",
    error: "bg-red-500/10 text-red-500 border-red-500/20",
    cancelled: "bg-zinc-500/10 text-zinc-500 border-zinc-500/20",
  }[status] || "bg-zinc-500/10 text-zinc-500 border-zinc-500/20";

  const labels = {
    running: "Processing",
    waiting: "Input Required",
    success: "Completed",
    error: "Failed",
    cancelled: "Cancelled"
  }[status] || status;

  return (
    <span className={cn(
      "px-2.5 py-0.5 rounded-full text-xs font-medium border uppercase tracking-wider",
      styles
    )}>
      {labels}
    </span>
  )
}
