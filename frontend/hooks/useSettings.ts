import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export interface SettingsResponse {
    music_library_path: string;
    source: "db" | "env" | "default";
}

export function useSettings() {
    const { data, error, isLoading, mutate } = useSWR<SettingsResponse>("/api/settings", fetcher);

    return {
        settings: data,
        isLoading,
        isError: error,
        mutate,
    };
}

export async function updateMusicLibraryPath(path: string) {
    const res = await fetch("/api/settings/music-library-path", {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ path }),
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to update settings");
    }

    return res.json();
}
