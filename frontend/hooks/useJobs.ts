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
            if (data && (data.current_state === "FINALIZED" || data.current_state.includes("FAILED"))) {
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
