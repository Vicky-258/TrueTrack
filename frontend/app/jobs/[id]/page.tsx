"use client";

import { useJob } from "@/hooks/useJobs";
import { JobDetailView } from "@/components/jobs/JobDetailView";
import { Loader2 } from "lucide-react";
import { useParams } from "next/navigation";

export default function JobDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const { job, isLoading, isError } = useJob(id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-zinc-500" size={24} />
      </div>
    );
  }

  if (isError || !job) {
    return (
      <div className="p-4 rounded-lg border border-red-900/50 bg-red-900/10 text-red-200">
        Failed to load job details.
      </div>
    );
  }

  return <JobDetailView job={job} />;
}
