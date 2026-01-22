"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { ArrowRight, CheckCircle2, XCircle, Clock, Disc3 } from "lucide-react";
import { cn } from "@/lib/utils";

export default function HistoryPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<any[]>("/jobs")
      .then(setJobs)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 animate-pulse space-y-4">
        <div className="w-12 h-12 rounded-full border-4 border-zinc-800 border-t-blue-500 animate-spin" />
        <p className="text-zinc-500 font-medium">Loading history...</p>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Download History</h1>
        <p className="text-muted-foreground">
          View and manage your recent downloads.
        </p>
      </header>

      <div className="grid gap-3">
        {jobs.length === 0 ? (
          <div className="text-center py-20 border border-dashed border-zinc-800 rounded-xl bg-zinc-900/30">
            <Disc3 className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-zinc-400">No jobs found</h3>
            <p className="text-zinc-500 text-sm mt-1">Start a new download to get started.</p>
            <Link href="/" className="inline-block mt-4 text-blue-400 hover:text-blue-300 text-sm font-medium">
              Start a download &rarr;
            </Link>
          </div>
        ) : (
          jobs.map((job) => (
            <Link
              key={job.job_id}
              href={`/jobs/${job.job_id}`}
              className="group relative flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-zinc-900/50 border border-zinc-800 hover:bg-zinc-900 hover:border-zinc-700 transition-all"
            >
              <div className="flex items-start gap-4">
                <StatusIcon status={job.status} />
                <div className="space-y-1">
                  <div className="font-semibold text-zinc-200 group-hover:text-white transition-colors">
                    {job.title || job.query || "Unknown Track"}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-zinc-500">
                    <span className="flex items-center gap-1">
                      <Clock size={12} />
                      {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                    </span>
                    <span className="w-1 h-1 rounded-full bg-zinc-700" />
                    <span className="font-mono text-zinc-600">
                      {job.state}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 text-sm md:text-right">
                {/* Optional: Add more info here, e.g. artist if available */}
                {job.artist && (
                  <div className="hidden md:block text-zinc-500 font-medium max-w-[150px] truncate">
                    {job.artist}
                  </div>
                )}

                <ArrowRight
                  size={18}
                  className="text-zinc-600 group-hover:text-blue-400 group-hover:translate-x-1 transition-all ml-auto md:ml-0"
                />
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'success') {
    return <div className="p-2 rounded-full bg-green-500/10 text-green-500"><CheckCircle2 size={20} /></div>
  }
  if (status === 'error' || status === 'cancelled') {
    return <div className="p-2 rounded-full bg-red-500/10 text-red-500"><XCircle size={20} /></div>
  }
  return <div className="p-2 rounded-full bg-blue-500/10 text-blue-500"><Disc3 size={20} className="animate-spin" /></div>
}
