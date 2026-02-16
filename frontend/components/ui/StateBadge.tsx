import { cn } from "@/lib/utils";

interface StateBadgeProps {
    state: string;
    className?: string;
}

const colorMap: Record<string, string> = {
    // Active states (Blue)
    default: "bg-zinc-800 text-zinc-400 border-zinc-700",
    active: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    finalized: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    failed: "bg-red-500/10 text-red-400 border-red-500/20",
    paused: "bg-amber-500/10 text-amber-400 border-amber-500/20",
};

export function StateBadge({ state, className }: StateBadgeProps) {
    const normalizedState = (state || "unknown").toLowerCase();

    // Map states to semantic styles defined in globals.css or Tailwind classes
    // Rules: Subtle background (10-15%), matching text, no pulse.
    let styles = "bg-zinc-500/10 text-zinc-400 border-zinc-500/20"; // Default/Pending

    if (["running", "downloading", "extracting", "encoding", "tagging"].some(s => normalizedState.includes(s))) {
        styles = "bg-indigo-500/15 text-indigo-400 border-indigo-500/20";
    } else if (normalizedState === "finalized" || normalizedState === "completed") {
        styles = "bg-emerald-500/15 text-emerald-400 border-emerald-500/20";
    } else if (normalizedState.includes("failed") || normalizedState.includes("error")) {
        styles = "bg-red-500/15 text-red-400 border-red-500/20";
    }

    return (
        <span className={cn(
            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors duration-200",
            styles,
            className
        )}>
            {state?.replace(/_/g, " ") || "Unknown"}
        </span>
    );
}
