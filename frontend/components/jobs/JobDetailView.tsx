import Link from "next/link";
import { ArrowLeft, Clock, FileAudio, AlertTriangle, PlayCircle } from "lucide-react";
import { JobStatusResponse } from "@/types/job";
import { StateBadge } from "@/components/ui/StateBadge";
import { JobTimeline } from "@/components/jobs/JobTimeline";
import { DebugPanel } from "@/components/jobs/DebugPanel";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

interface JobDetailViewProps {
    job: JobStatusResponse;
}

export function JobDetailView({ job }: JobDetailViewProps) {
    const isFailed = job.state.toLowerCase().includes("failed");

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex flex-col gap-4 border-b border-zinc-800 pb-6">
                <Link href="/jobs" className="text-sm text-zinc-500 hover:text-zinc-300 flex items-center gap-1 w-fit transition-colors">
                    <ArrowLeft size={14} /> Back to jobs
                </Link>

                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">{job.title || "Untitled Job"}</h1>
                        <p className="text-zinc-500 text-sm mt-1">{job.artist || "Unknown Artist"}</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="text-xs text-zinc-600 font-mono">
                            ID: {job.job_id.slice(0, 8)}
                        </div>
                        <StateBadge state={job.state} className="text-sm px-3 py-1" />
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">

                    {/* Error Banner */}
                    {isFailed && job.error_message && (
                        <div className="rounded-lg border border-red-900/50 bg-red-900/10 p-4 text-sm text-red-200 flex gap-3 items-start">
                            <AlertTriangle className="shrink-0 mt-0.5" size={16} />
                            <div className="space-y-1">
                                <p className="font-semibold">Job Failed</p>
                                <p className="opacity-90">{job.error_message}</p>
                                {job.error_code && <p className="font-mono text-xs opacity-70">Code: {job.error_code}</p>}
                            </div>
                        </div>
                    )}

                    {/* Result Success */}
                    {job.result?.path && (
                        <div className="rounded-lg border border-emerald-900/50 bg-emerald-900/10 p-4 text-sm text-emerald-200 flex gap-3 items-center">
                            <FileAudio className="shrink-0" size={18} />
                            <div className="flex-1 min-w-0">
                                <p className="font-medium">Downloading & Processing Complete</p>
                                <p className="opacity-70 truncate font-mono text-xs mt-1">{job.result.path}</p>
                            </div>
                        </div>
                    )}

                    {/* Info Cards */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/30">
                            <p className="text-xs text-zinc-500 uppercase tracking-wider font-semibold mb-2">Resume Point</p>
                            <div className="flex items-center gap-2 text-zinc-300">
                                <PlayCircle size={16} />
                                <span className="font-mono text-sm">{job.resume_from || "None"}</span>
                            </div>
                        </div>
                        <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/30">
                            <p className="text-xs text-zinc-500 uppercase tracking-wider font-semibold mb-2">Retry Count</p>
                            <div className="flex items-center gap-2 text-zinc-300">
                                <Clock size={16} />
                                <span className="font-mono text-sm">{job.retry_count}</span>
                            </div>
                        </div>
                    </div>

                    <DebugPanel data={job} className="mt-8" />
                </div>

                {/* Sidebar / Timeline */}
                <div className="lg:col-span-1">
                    <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-6">
                        <h3 className="text-sm font-semibold text-zinc-400 mb-6 uppercase tracking-wider">Progress</h3>
                        <JobTimeline job={job} />
                    </div>
                </div>
            </div>
        </div>
    );
}
