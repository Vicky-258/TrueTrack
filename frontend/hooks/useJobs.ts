import useSWR from "swr";
import { JobStatusResponse } from "@/types/job";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function useJobs() {
    const { data, error, isLoading } = useSWR<JobStatusResponse[]>("/api/jobs", fetcher, {
        refreshInterval: 2000,
    });

    return {
        jobs: data,
        isLoading,
        isError: error,
    };
}

export function useJob(id: string) {
    const { data, error, isLoading } = useSWR<JobStatusResponse>(id ? `/api/jobs/${id}` : null, fetcher, {
        refreshInterval: (data) => {
            // Stop polling if finalized or failed
            if (data && (data.state === "FINALIZED" || data.state.includes("FAILED"))) {
                return 0;
            }
            return 2000;
        }
    });

    return {
        job: data,
        isLoading,
        isError: error,
    };
}

export async function submitJobInput(jobId: string, choiceIndex: number) {
    const res = await fetch(`/api/jobs/${jobId}/input`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ choice: choiceIndex }),
    });

    if (!res.ok) {
        throw new Error("Failed to submit input");
    }

    return res.json();
}

export async function cancelJob(jobId: string) {
    const res = await fetch(`/api/jobs/${jobId}/cancel`, {
        method: "POST",
    });

    if (!res.ok) {
        throw new Error("Failed to cancel job");
    }

    return res.json();
}

export async function resumeJob(jobId: string) {
    const res = await fetch(`/api/jobs/${jobId}/resume`, {
        method: "POST",
    });

    if (!res.ok) {
        throw new Error("Failed to resume job");
    }

    return res.json();
}
