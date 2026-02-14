"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
    LayoutDashboard,
    Archive,
    Settings,
    Disc3
} from "lucide-react";

const navigation = [
    { name: "Active Jobs", href: "/jobs", icon: LayoutDashboard },
    { name: "Archived", href: "/archived", icon: Archive },
    { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <div className="flex h-screen flex-col border-r border-zinc-800 bg-zinc-950 w-64 fixed left-0 top-0 z-40">
            <div className="flex h-16 items-center px-6 border-b border-zinc-800/50">
                <Link href="/" className="flex items-center gap-2 font-semibold text-zinc-100 hover:opacity-80 transition-opacity">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-100 text-zinc-950">
                        <Disc3 size={18} className="animate-spin-slow" />
                    </div>
                    <span>TrueTrack</span>
                </Link>
            </div>

            <div className="flex-1 overflow-y-auto py-6 px-3">
                <nav className="flex flex-col gap-1">
                    {navigation.map((item) => {
                        const isActive = pathname.startsWith(item.href);
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={cn(
                                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                                    isActive
                                        ? "bg-zinc-800/50 text-zinc-100"
                                        : "text-zinc-500 hover:bg-zinc-900 hover:text-zinc-300"
                                )}
                            >
                                <item.icon size={16} />
                                {item.name}
                            </Link>
                        );
                    })}
                </nav>
            </div>

            <div className="p-4 border-t border-zinc-800/50">
                <div className="text-xs text-zinc-600 text-center">
                    v0.1.0-beta
                </div>
            </div>
        </div>
    );
}
