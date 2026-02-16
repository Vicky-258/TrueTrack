"use client";

import { useJobs } from "@/hooks/useJobs";
import { JobCard } from "@/components/jobs/JobCard";
import { Loader2, Archive } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export default function ArchivedPage() {
    const { jobs, isLoading, isError } = useJobs();

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="animate-spin text-muted-foreground" size={24} />
            </div>
        );
    }

    if (isError) {
        return (
            <Card className="border-destructive/50 bg-destructive/10">
                <CardContent className="p-4 text-destructive">
                    Failed to load jobs.
                </CardContent>
            </Card>
        );
    }

    const archivedJobs = (jobs || []).filter(j => j.archived || j.state === "FINALIZED");

    const sortedJobs = [...archivedJobs].sort((a, b) => {
        const aTime = Math.max(...Object.values({ ...a.step_started_at, ...a.step_finished_at }).map(t => new Date(t).getTime()));
        const bTime = Math.max(...Object.values({ ...b.step_started_at, ...b.step_finished_at }).map(t => new Date(t).getTime()));
        return bTime - aTime;
    });

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-2">
                <div className="p-2 bg-muted/20 rounded-lg text-muted-foreground">
                    <Archive size={20} />
                </div>
                <h1 className="text-2xl font-semibold tracking-tight text-foreground">Archived Jobs</h1>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {sortedJobs.map((job) => (
                    <JobCard key={job.job_id} job={job} />
                ))}
                {sortedJobs.length === 0 && (
                    <div className="col-span-full py-12 text-center text-muted-foreground border border-dashed border-border rounded-xl">
                        No archived jobs found
                    </div>
                )}
            </div>
        </div>
    );
}
