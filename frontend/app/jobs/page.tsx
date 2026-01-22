"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type JobSummary = {
  job_id: string;
  status: "running" | "waiting" | "success" | "error" | "cancelled";
  state: string;
  title?: string;
  artist?: string;
  created_at: string;
  last_message?: string;
  can_resume?: boolean; // expose later from backend (optional)
};

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<JobSummary[]>("/jobs").then((data) => {
      setJobs(data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="p-6">Loading jobs…</div>;
  }

  return (
    <main className="p-6 space-y-4 max-w-3xl mx-auto">
      <h1 className="text-xl font-semibold">Job History</h1>

      {jobs.length === 0 && (
        <div className="text-zinc-400">No jobs yet</div>
      )}

      <div className="space-y-3">
        {jobs.map((job) => {
          const isOpen = expanded === job.job_id;

          return (
            <div
              key={job.job_id}
              className="rounded bg-zinc-800 overflow-hidden"
            >
              {/* ---------- COLLAPSED HEADER ---------- */}
              <button
                onClick={() =>
                  setExpanded(isOpen ? null : job.job_id)
                }
                className="w-full p-4 flex justify-between items-center hover:bg-zinc-700"
              >
                <div className="text-left">
                  <div className="font-semibold">
                    {job.title ?? "Untitled"}
                  </div>
                  <div className="text-sm text-zinc-400">
                    {job.artist ?? "Unknown artist"}
                  </div>
                </div>

                <span
                  className={`text-xs px-2 py-1 rounded ${
                    job.status === "success"
                      ? "bg-green-800 text-green-200"
                      : job.status === "error"
                      ? "bg-red-800 text-red-200"
                      : job.status === "cancelled"
                      ? "bg-yellow-800 text-yellow-200"
                      : "bg-blue-800 text-blue-200"
                  }`}
                >
                  {job.status}
                </span>
              </button>

              {/* ---------- EXPANDED DETAILS ---------- */}
              {isOpen && (
                <div className="p-4 border-t border-zinc-700 space-y-3 text-sm">
                  <div className="text-zinc-400">
                    State: <b>{job.state}</b>
                  </div>

                  {job.last_message && (
                    <div className="text-zinc-300">
                      {job.last_message}
                    </div>
                  )}

                  <div className="flex gap-2 flex-wrap pt-2">
                    <Link
                      href={`/jobs/${job.job_id}`}
                      className="px-3 py-1 rounded bg-zinc-700 hover:bg-zinc-600"
                    >
                      View
                    </Link>

                    {job.status === "cancelled" && job.can_resume && (
                      <button
                        className="px-3 py-1 rounded bg-green-700 hover:bg-green-600"
                        onClick={async () => {
                          await api(
                            `/jobs/${job.job_id}/resume`,
                            { method: "POST" }
                          );
                          location.reload();
                        }}
                      >
                        Resume
                      </button>
                    )}
                  </div>

                  <div className="text-xs text-zinc-500 font-mono">
                    {job.job_id}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </main>
  );
}
