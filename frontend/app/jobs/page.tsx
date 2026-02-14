"use client";

import { useJobs } from "@/hooks/useJobs";
import { JobCard } from "@/components/jobs/JobCard";
import { Loader2, Plus } from "lucide-react";
import Link from "next/link";
import { JobStatusResponse } from "@/types/job";

export default function JobsPage() {
  const { jobs, isLoading, isError } = useJobs();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-zinc-500" size={24} />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-4 rounded-lg border border-red-900/50 bg-red-900/10 text-red-200">
        Failed to load jobs. Is the backend running?
      </div>
    );
  }

  // Filter active vs completed could be done here or in separate tabs, 
  // but for now just list all as per request "Jobs List Page"

  const sortedJobs = [...(jobs || [])].sort((a, b) => {
    // Sort by most recent activity
    const aTime = Math.max(...Object.values({ ...a.step_started_at, ...a.step_finished_at }).map(t => new Date(t).getTime()));
    const bTime = Math.max(...Object.values({ ...b.step_started_at, ...b.step_finished_at }).map(t => new Date(t).getTime()));
    return bTime - aTime;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Jobs</h1>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-zinc-100 text-zinc-900 text-sm font-medium hover:bg-zinc-200 transition-colors"
        >
          <Plus size={16} />
          New Job
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sortedJobs.map((job) => (
          <JobCard key={job.job_id} job={job} />
        ))}
        {sortedJobs.length === 0 && (
          <div className="col-span-full py-12 text-center text-zinc-500 border border-dashed border-zinc-800 rounded-xl">
            No jobs found
          </div>
        )}
      </div>
    </div>
  );
}
