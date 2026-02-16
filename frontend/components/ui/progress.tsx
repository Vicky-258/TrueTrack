import * as React from "react";
import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

export interface Step {
    id: string;
    label: string;
    status: "pending" | "current" | "completed" | "error";
}

interface ProgressProps {
    steps: Step[];
    className?: string;
}

export function Progress({ steps, className }: ProgressProps) {
    return (
        <div className={cn("relative flex flex-col space-y-0", className)}>
            {steps.map((step, index) => {
                const isLast = index === steps.length - 1;

                return (
                    <div key={step.id} className="relative flex min-h-[48px]">
                        {/* Connector Line */}
                        {!isLast && (
                            <div className="absolute left-3 top-7 bottom-0 w-[2px] bg-zinc-800">
                                {/* Animated fill for connector */}
                                <div
                                    className={cn(
                                        "w-full bg-indigo-500 transition-all duration-300 ease-out",
                                        step.status === "completed" ? "h-full" : "h-0"
                                    )}
                                />
                            </div>
                        )}

                        <div className="flex flex-col">
                            <div className="flex items-center">
                                {/* Indicator Circle */}
                                <div className={cn(
                                    "relative z-10 flex h-6 w-6 items-center justify-center rounded-full border text-xs transition-all duration-200",
                                    step.status === "completed" ? "bg-indigo-500 border-indigo-500 text-white" :
                                        step.status === "current" ? "border-indigo-500 bg-zinc-900 ring-2 ring-indigo-500/20" :
                                            step.status === "error" ? "border-red-500 bg-red-500/10 text-red-500" :
                                                "border-zinc-700 bg-zinc-900 text-zinc-500"
                                )}>
                                    {step.status === "completed" && (
                                        <Check className="h-3.5 w-3.5 animate-in fade-in duration-200" />
                                    )}
                                    {step.status === "current" && (
                                        <div className="h-2 w-2 rounded-full bg-indigo-500 animate-in zoom-in duration-200" />
                                    )}
                                    {step.status === "error" && (
                                        <span className="text-[10px] font-bold">!</span>
                                    )}
                                </div>

                                <span className={cn(
                                    "ml-3 text-sm font-medium transition-colors duration-200",
                                    step.status === "current" ? "text-indigo-400" :
                                        step.status === "completed" ? "text-zinc-400" :
                                            "text-zinc-600"
                                )}>
                                    {step.label}
                                </span>
                            </div>

                            {/* Spacer to maintain vertical rhythm if content is added later */}
                            {!isLast && <div className="h-4" />}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
