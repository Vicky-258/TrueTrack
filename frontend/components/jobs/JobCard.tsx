import Link from "next/link";
import { Clock, RotateCcw, AlertTriangle, FileAudio } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { type JobStatusResponse } from "@/types/job";
import { StateBadge } from "@/components/ui/StateBadge";
import { cn } from "@/lib/utils";

interface JobCardProps {
    job: JobStatusResponse;
}

export function JobCard({ job }: JobCardProps) {
    // Determine if we should show a specific icon based on state
    const isFailed = job.current_state.toLowerCase().includes("failed");
    const isPaused = job.current_state.toLowerCase().includes("paused");

    // Find the latest step timestamp for "Updated x ago"
    const timestamps = { ...job.step_started_at, ...job.step_finished_at };
    const latestTimestamp = Object.values(timestamps).sort().pop();

    return (
        <Link
            href={`/jobs/${job.job_id}`}
            className="block group"
        >
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5 hover:bg-zinc-900/80 hover:border-zinc-700 transition-all cursor-pointer">
                <div className="flex justify-between items-start mb-3">
                    <div className="flex flex-col gap-1">
                        <h3 className="font-medium text-zinc-100 group-hover:text-white truncate max-w-[300px] sm:max-w-md">
                            {job.title || "Unknown Title"}
                        </h3>
                        <p className="text-sm text-zinc-500">{job.artist || "Unknown Artist"}</p>
                    </div>
                    <StateBadge state={job.current_state} />
                </div>

                <div className="flex items-center gap-4 text-xs text-zinc-500 mt-4">
                    {latestTimestamp && (
                        <div className="flex items-center gap-1.5">
                            <Clock size={14} />
                            <span>{formatDistanceToNow(new Date(latestTimestamp), { addSuffix: true })}</span>
                        </div>
                    )}

                    {job.retry_count > 0 && (
                        <div className={cn("flex items-center gap-1.5", isFailed ? "text-red-400" : "text-amber-400")}>
                            <RotateCcw size={14} />
                            <span>{job.retry_count} retries</span>
                        </div>
                    )}

                    {job.result?.path && (
                        <div className="flex items-center gap-1.5 text-emerald-500/80">
                            <FileAudio size={14} />
                            <span>Ready</span>
                        </div>
                    )}
                </div>
            </div>
        </Link>
    );
}
