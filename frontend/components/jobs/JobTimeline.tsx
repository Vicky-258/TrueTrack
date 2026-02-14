import { Check, Circle, Loader2, XCircle, PauseCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { type JobStatusResponse } from "@/types/job";
import { format } from "date-fns";

interface JobTimelineProps {
    job: JobStatusResponse;
}

const STEPS = ["PENDING", "DOWNLOADING", "EXTRACTING", "ENCODING", "TAGGING", "FINALIZED"];

export function JobTimeline({ job }: JobTimelineProps) {
    const currentState = job.current_state.toUpperCase();
    const history = job.step_finished_at || {};
    const started = job.step_started_at || {};

    // Helper to determine step status
    const getStepStatus = (step: string, index: number) => {
        // Exact match
        if (currentState === step) return "active";
        if (currentState.includes("FAILED") && STEPS[index] === currentState.split("_")[0]) return "failed";

        // Past completed steps
        if (history[step.toLowerCase()]) return "completed";

        // Check previous steps completion for current active context
        // E.g. if we are ENCODING, then DOWNLOADING and EXTRACTING are strictly completed (or skipped if logic allows, but linear here)
        // Simpler: if index < current_step_index, it's completed? 
        // Not always reliable with non-linear or complex states, but mostly true for this linear pipeline.
        // Let's rely on timestamps.
        const isCompleted = !!history[step.toLowerCase()];
        if (isCompleted) return "completed";

        // Current state handling for partial matches (e.g. RETRY_PAUSED in downloading)
        if (currentState.includes(step) || (currentState.includes("PAUSED") && currentState.includes(step))) {
            return "active";
        }

        return "upcoming";
    };

    return (
        <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-px bg-zinc-800" />

            <div className="space-y-8 relative">
                {STEPS.map((step, index) => {
                    const status = getStepStatus(step, index);
                    const startTime = started[step.toLowerCase()];
                    const endTime = history[step.toLowerCase()];

                    return (
                        <div key={step} className="flex gap-4">
                            <div className={cn(
                                "relative z-10 flex h-8 w-8 items-center justify-center rounded-full border-2 transition-colors bg-zinc-950",
                                status === "completed" ? "border-emerald-500/50 text-emerald-500" :
                                    status === "active" ? "border-blue-500 text-blue-500" :
                                        status === "failed" ? "border-red-500 text-red-500" :
                                            "border-zinc-800 text-zinc-700"
                            )}>
                                {status === "completed" && <Check size={14} />}
                                {status === "active" && <Loader2 size={14} className="animate-spin" />}
                                {status === "failed" && <XCircle size={14} />}
                                {status === "upcoming" && <Circle size={10} />}
                            </div>

                            <div className="flex flex-col pt-1">
                                <span className={cn(
                                    "text-sm font-medium",
                                    status === "completed" ? "text-zinc-300" :
                                        status === "active" ? "text-blue-400" :
                                            status === "failed" ? "text-red-400" :
                                                "text-zinc-600"
                                )}>
                                    {step}
                                </span>

                                {(startTime || endTime) && (
                                    <div className="flex flex-col gap-0.5 mt-1 text-[10px] text-zinc-600 font-mono">
                                        {startTime && <span>Started: {format(new Date(startTime), "HH:mm:ss")}</span>}
                                        {endTime && <span>Finished: {format(new Date(endTime), "HH:mm:ss")}</span>}
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
