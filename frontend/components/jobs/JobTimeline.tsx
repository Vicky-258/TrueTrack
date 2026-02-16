import { type JobStatusResponse } from "@/types/job";
import { Progress, type Step } from "@/components/ui/progress";
import { format } from "date-fns";

interface JobTimelineProps {
    job: JobStatusResponse;
}

const STEPS = ["PENDING", "DOWNLOADING", "EXTRACTING", "ENCODING", "TAGGING", "FINALIZED"];

export function JobTimeline({ job }: JobTimelineProps) {
    const currentState = job.state.toUpperCase();
    const history = job.step_finished_at || {};
    const started = job.step_started_at || {};

    // Map strict job steps to Progress component steps
    const progressSteps: Step[] = STEPS.map((step, index) => {
        let status: Step["status"] = "pending";

        // Logic to determine status
        const isCurrent = currentState === step || (currentState.includes(step) && !currentState.includes("FAILED"));
        const isPast = !!history[step.toLowerCase()];
        const isFailed = currentState.includes("FAILED") && currentState.startsWith(step);

        if (isFailed) status = "error";
        else if (isPast) status = "completed";
        else if (isCurrent) status = "current";

        // Special case for FINALIZED
        if (step === "FINALIZED" && currentState === "FINALIZED") status = "completed";

        return {
            id: step,
            label: step,
            status: status
        };
    });

    return (
        <div className="py-2">
            <Progress steps={progressSteps} />

            {/* Optional: Detailed timestamps could be a separate component or tooltip, 
                but keeping the timeline clean as per constitution. 
                If timestamps are critical, we might need a custom variant of Progress, 
                but for now, simpler is better. */
            }
        </div>
    );
}
