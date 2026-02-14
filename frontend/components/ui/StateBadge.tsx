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
    const normalizedState = state.toLowerCase();

    let variant = "default";

    if (["downloading", "extracting", "encoding", "tagging", "pending"].some(s => normalizedState.includes(s))) {
        variant = "active";
    } else if (normalizedState === "finalized") {
        variant = "finalized";
    } else if (normalizedState.includes("failed")) {
        variant = "failed";
    } else if (normalizedState.includes("paused") || normalizedState.includes("retry")) {
        variant = "paused";
    }

    const styles = colorMap[variant] || colorMap.default;

    return (
        <span className={cn(
            "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
            styles,
            className
        )}>
            {state.replace(/_/g, " ")}
        </span>
    );
}
