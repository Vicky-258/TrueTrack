import Link from "next/link";
import { ArrowLeft, Clock, FileAudio, AlertTriangle, PlayCircle } from "lucide-react";
import { JobStatusResponse } from "@/types/job";
import { StateBadge } from "@/components/ui/StateBadge";
import { JobTimeline } from "@/components/jobs/JobTimeline";
import { DebugPanel } from "@/components/jobs/DebugPanel";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { format } from "date-fns";
import { JobInputSelection } from "@/components/jobs/JobInputSelection";
import { submitJobInput, cancelJob, resumeJob } from "@/hooks/useJobs";
import { mutate } from "swr"; // Import mutate to refresh
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Play, XCircle } from "lucide-react";

interface JobDetailViewProps {
    job: JobStatusResponse;
}

export function JobDetailView({ job }: JobDetailViewProps) {
    const isFailed = job.state.toLowerCase().includes("failed");

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex flex-col gap-4 border-b border-border pb-6">
                <Link href="/jobs" className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 w-fit transition-colors">
                    <ArrowLeft size={14} /> Back to jobs
                </Link>

                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-2xl font-bold text-foreground tracking-tight">{job.title || "Untitled Job"}</h1>
                        <p className="text-muted-foreground text-sm mt-1">{job.artist || "Unknown Artist"}</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="text-xs text-muted-foreground font-mono">
                            ID: {job.job_id.slice(0, 8)}
                        </div>
                        <StateBadge state={job.state} className="text-sm px-3 py-1" />
                    </div>
                </div>

                {/* Actions Toolbar */}
                <div className="flex items-center gap-3">
                    {/* Cancel Action */}
                    {(job.status === "running" || job.status === "waiting") && (
                        <Button
                            variant="destructive"
                            size="sm"
                            onClick={async () => {
                                await cancelJob(job.job_id);
                                mutate(`/api/jobs/${job.job_id}`);
                            }}
                        >
                            <XCircle size={16} className="mr-2" />
                            Cancel Job
                        </Button>
                    )}

                    {/* Resume Action */}
                    {job.can_resume && (
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={async () => {
                                await resumeJob(job.job_id);
                                mutate(`/api/jobs/${job.job_id}`);
                            }}
                            className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 border-emerald-500/20"
                        >
                            <Play size={16} className="mr-2" />
                            Resume Job
                        </Button>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">

                    {/* Input Selection */}
                    {job.input_required && (
                        <JobInputSelection
                            job={job}
                            onSelect={async (index) => {
                                await submitJobInput(job.job_id, index);
                                await mutate(`/api/jobs/${job.job_id}`); // Refresh the specific job
                                await mutate("/api/jobs"); // Refresh the list
                            }}
                        />
                    )}

                    {/* Error Banner */}
                    {isFailed && job.error_message && (
                        <Card className="border-destructive/30 bg-destructive/5">
                            <CardContent className="p-4 flex gap-3 items-start text-destructive">
                                <AlertTriangle className="shrink-0 mt-0.5" size={16} />
                                <div className="space-y-1">
                                    <p className="font-semibold text-sm">Job Failed</p>
                                    <p className="opacity-90 text-sm">{job.error_message}</p>
                                    {job.error_code && <p className="font-mono text-xs opacity-70">Code: {job.error_code}</p>}
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Result Success */}
                    {job.result?.path && (
                        <Card className="border-emerald-500/30 bg-emerald-500/5">
                            <CardContent className="p-4 flex gap-3 items-center text-emerald-500">
                                <FileAudio className="shrink-0" size={18} />
                                <div className="flex-1 min-w-0">
                                    <p className="font-medium text-sm">Downloading & Processing Complete</p>
                                    <p className="opacity-70 truncate font-mono text-xs mt-1">{job.result.path}</p>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Info Cards */}
                    <div className="grid grid-cols-2 gap-4">
                        <Card className="bg-muted/10 border-border/50 shadow-none">
                            <CardContent className="p-4">
                                <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-2">Resume Point</p>
                                <div className="flex items-center gap-2 text-foreground">
                                    <PlayCircle size={16} />
                                    <span className="font-mono text-sm">{job.resume_from || "None"}</span>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="bg-muted/10 border-border/50 shadow-none">
                            <CardContent className="p-4">
                                <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-2">Retry Count</p>
                                <div className="flex items-center gap-2 text-foreground">
                                    <Clock size={16} />
                                    <span className="font-mono text-sm">{job.retry_count}</span>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    <DebugPanel data={job} className="mt-8" />
                </div>

                {/* Sidebar / Timeline */}
                <div className="lg:col-span-1">
                    <Card>
                        <CardContent className="p-6">
                            <h3 className="text-xs font-semibold text-muted-foreground mb-6 uppercase tracking-wider">Progress</h3>
                            <JobTimeline job={job} />
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
