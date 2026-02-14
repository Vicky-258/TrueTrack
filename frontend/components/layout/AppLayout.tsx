import { Sidebar } from "./Sidebar";

export function AppLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-200 selection:bg-zinc-800 selection:text-zinc-100 font-sans antialiased">
            <Sidebar />
            <main className="pl-64 min-h-screen">
                <div className="container max-w-5xl mx-auto py-10 px-8">
                    {children}
                </div>
            </main>
        </div>
    );
}
