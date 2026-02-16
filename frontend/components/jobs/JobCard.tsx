import Link from "next/link";
import { Clock, RotateCcw, AlertTriangle, FileAudio } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { type JobStatusResponse } from "@/types/job";
import { StateBadge } from "@/components/ui/StateBadge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface JobCardProps {
    job: JobStatusResponse;
}

export function JobCard({ job }: JobCardProps) {
    // Determine if we should show a specific icon based on state
    const isFailed = job.state.toLowerCase().includes("failed");
    const isPaused = job.state.toLowerCase().includes("paused");

    // Find the latest step timestamp for "Updated x ago"
    const timestamps = { ...job.step_started_at, ...job.step_finished_at };
    const latestTimestamp = Object.values(timestamps).sort().pop();

    return (
        <Link href={`/jobs/${job.job_id}`} className="block group">
            <Card className="h-full hover:border-primary/20 transition-all">
                <div className="p-5">
                    <div className="flex justify-between items-start mb-3">
                        <div className="flex flex-col gap-1 overflow-hidden pr-2">
                            <h3 className="font-medium text-foreground group-hover:text-primary transition-colors truncate">
                                {job.title || "Unknown Title"}
                            </h3>
                            <p className="text-sm text-muted-foreground truncate">{job.artist || "Unknown Artist"}</p>
                        </div>
                        <StateBadge state={job.state} className="shrink-0" />
                    </div>

                    <div className="flex items-center gap-4 text-xs text-muted-foreground mt-4">
                        {latestTimestamp && (
                            <div className="flex items-center gap-1.5">
                                <Clock size={14} />
                                <span>{formatDistanceToNow(new Date(latestTimestamp), { addSuffix: true })}</span>
                            </div>
                        )}

                        {job.retry_count > 0 && (
                            <div className={cn("flex items-center gap-1.5", isFailed ? "text-destructive" : "text-amber-500")}>
                                <RotateCcw size={14} />
                                <span>{job.retry_count} retries</span>
                            </div>
                        )}

                        {job.result?.path && (
                            <div className="flex items-center gap-1.5 text-emerald-500">
                                <FileAudio size={14} />
                                <span>Ready</span>
                            </div>
                        )}
                    </div>
                </div>
            </Card>
        </Link>
    );
}
