"use client";

import { Settings, Save } from "lucide-react";

export default function SettingsPage() {
    return (
        <div className="space-y-8 max-w-2xl">
            <div className="flex items-center gap-2">
                <div className="p-2 bg-zinc-900 rounded-lg text-zinc-400">
                    <Settings size={20} />
                </div>
                <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
            </div>

            <div className="space-y-6">
                <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/20 space-y-4">
                    <h3 className="font-medium text-zinc-200">General Configuration</h3>

                    <div className="space-y-2">
                        <label className="text-sm text-zinc-400">Download Path</label>
                        <div className="flex items-center gap-2">
                            <input
                                type="text"
                                value="/home/user/Music"
                                readOnly
                                className="flex-1 bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                            />
                        </div>
                        <p className="text-xs text-zinc-600">
                            Defined in backend environment variables.
                        </p>
                    </div>
                </div>

                <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/20 space-y-4">
                    <h3 className="font-medium text-zinc-200">Appearance</h3>

                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                            <label className="text-sm text-zinc-300">Dark Mode</label>
                            <p className="text-xs text-zinc-500">Always enabled for eye comfort</p>
                        </div>
                        <div className="h-6 w-10 rounded-full bg-blue-500/20 border border-blue-500/50 relative">
                            <div className="absolute right-1 top-1 h-3.5 w-3.5 rounded-full bg-blue-400" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
