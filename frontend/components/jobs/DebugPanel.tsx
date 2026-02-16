"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";

interface DebugPanelProps {
    data: any;
    title?: string;
    className?: string;
}

export function DebugPanel({ data, title = "Debug Info", className }: DebugPanelProps) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className={cn("rounded-lg border border-border bg-muted/30 overflow-hidden", className)}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
            >
                {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                <Terminal size={12} />
                {title}
            </button>

            {isOpen && (
                <div className="p-3 bg-card border-t border-border overflow-x-auto">
                    <pre className="text-[10px] leading-relaxed font-mono text-muted-foreground">
                        {JSON.stringify(data, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
}
