"use client";

import { useState } from "react";
import { Check, Music2, User, Disc, Clock, Film } from "lucide-react";
import { cn } from "@/lib/utils";
import { JobStatusResponse } from "@/types/job";
import { Button } from "@/components/ui/button";

interface JobInputSelectionProps {
    job: JobStatusResponse;
    onSelect: (choiceIndex: number) => Promise<void>;
}

export function JobInputSelection({ job, onSelect }: JobInputSelectionProps) {
    const [submitting, setSubmitting] = useState<number | null>(null);

    if (!job.input_required) return null;

    const { type, choices } = job.input_required;

    const handleSelect = async (index: number) => {
        setSubmitting(index);
        try {
            await onSelect(index);
        } finally {
            setSubmitting(null);
        }
    };

    if (type === "user_intent_selection") {
        return (
            <div className="space-y-4 animate-in slide-in-from-bottom-4 duration-500">
                <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4 mb-6">
                    <h3 className="text-amber-500 font-semibold mb-1 text-sm">Select Correct Song</h3>
                    <p className="text-amber-500/70 text-sm">
                        Multiple matches found. Please select the correct song to proceed.
                    </p>
                </div>

                <div className="grid gap-3">
                    {choices.map((choice, idx) => (
                        <div
                            key={idx}
                            onClick={() => handleSelect(idx)}
                            className={cn(
                                "group relative overflow-hidden rounded-xl border border-border bg-card p-4 cursor-pointer transition-all hover:border-primary/50 hover:bg-accent/50",
                                submitting === idx && "opacity-70 pointer-events-none"
                            )}
                        >
                            <div className="flex justify-between items-start gap-4">
                                <div className="space-y-1 min-w-0">
                                    <h4 className="font-medium text-foreground truncate pr-8">
                                        {choice.title || "Unknown Title"}
                                    </h4>

                                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                                        {choice.artists && choice.artists.length > 0 && (
                                            <div className="flex items-center gap-1.5">
                                                <User size={12} />
                                                <span className="truncate max-w-[150px]">
                                                    {choice.artists.join(", ")}
                                                </span>
                                            </div>
                                        )}
                                        {choice.album && (
                                            <div className="flex items-center gap-1.5">
                                                <Disc size={12} />
                                                <span className="truncate max-w-[150px]">{choice.album}</span>
                                            </div>
                                        )}
                                        {choice.duration && (
                                            <div className="flex items-center gap-1.5">
                                                <Clock size={12} />
                                                <span>{Math.floor(choice.duration / 60)}:{(choice.duration % 60).toString().padStart(2, '0')}</span>
                                            </div>
                                        )}
                                    </div>

                                    {choice.video_id && (
                                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground/70 mt-2 font-mono">
                                            <Film size={12} />
                                            <span>{choice.video_id}</span>
                                        </div>
                                    )}
                                </div>

                                <Button
                                    size="sm"
                                    disabled={submitting !== null}
                                    className={cn(
                                        "shrink-0 transition-opacity",
                                        submitting === idx ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                                    )}
                                >
                                    {submitting === idx ? "Selecting..." : "Select"}
                                </Button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (type === "user_metadata_selection") {
        return (
            <div className="space-y-4 animate-in slide-in-from-bottom-4 duration-500">
                <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-lg p-4 mb-6">
                    <h3 className="text-indigo-500 font-semibold mb-1 text-sm">Select Best Metadata</h3>
                    <p className="text-indigo-500/70 text-sm">
                        Please confirm the best metadata match for this track.
                    </p>
                </div>

                <div className="grid gap-3">
                    {choices.map((choice, idx) => (
                        <div
                            key={idx}
                            onClick={() => handleSelect(idx)}
                            className={cn(
                                "group relative overflow-hidden rounded-xl border border-border bg-card p-4 cursor-pointer transition-all hover:border-primary/50 hover:bg-accent/50",
                                submitting === idx && "opacity-70 pointer-events-none"
                            )}
                        >
                            <div className="flex items-start gap-4">
                                {choice.artworkUrl100 && (
                                    <img
                                        src={choice.artworkUrl100}
                                        alt="Album Art"
                                        className="w-16 h-16 rounded-md object-cover bg-muted"
                                    />
                                )}
                                <div className="flex-1 min-w-0 space-y-1">
                                    <h4 className="font-medium text-foreground truncate">
                                        {choice.trackName || "Unknown Track"}
                                    </h4>
                                    <div className="text-sm text-muted-foreground truncate">
                                        {choice.artistName}
                                    </div>
                                    <div className="text-xs text-muted-foreground/80 truncate">
                                        {choice.collectionName} • {choice.releaseDate?.split('-')[0]}
                                    </div>
                                </div>
                                <Button
                                    size="sm"
                                    className={cn(
                                        "shrink-0 self-center transition-opacity",
                                        submitting === idx ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                                    )}
                                >
                                    {submitting === idx ? "Selecting..." : "Select"}
                                </Button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="p-4 border border-border rounded-lg bg-muted/50 text-muted-foreground text-sm">
            Unknown input type: {type}
        </div>
    );
}
