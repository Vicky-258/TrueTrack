export interface JobStatusResponse {
    job_id: string;
    title: string;
    artist: string;
    state: string;
    status: string;
    retry_count: number;
    resume_from: string | null;
    error_code: string | null;
    error_message: string | null;
    step_started_at: Record<string, string>;
    step_finished_at: Record<string, string>;
    metadata_confidence: number | null;
    archived: boolean;
    can_resume?: boolean;
    input_required?: {
        type: string;
        choices: any[];
    };
    result: {
        path: string | null
    }
}
