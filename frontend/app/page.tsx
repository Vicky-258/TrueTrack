"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ArrowRight, Settings2, CloudDownload, Terminal, Archive, Sparkles } from "lucide-react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";

export default function Home() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [showOptions, setShowOptions] = useState(false);

  // Options state
  const [ask, setAsk] = useState(true);
  const [dryRun, setDryRun] = useState(false);
  const [forceArchive, setForceArchive] = useState(false);
  const [verbose, setVerbose] = useState(false);

  // Recent jobs
  const [recentJobs, setRecentJobs] = useState<any[]>([]);

  const router = useRouter();

  useEffect(() => {
    // Optimistic check for recent jobs in session or just fetch last 3
    api<any[]>("/jobs").then((jobs) => {
      setRecentJobs(jobs.slice(0, 3));
    }).catch(() => { });
  }, []);

  async function submit() {
    if (!query.trim()) return;

    setLoading(true);

    try {
      const job = await api<any>("/jobs", {
        method: "POST",
        body: JSON.stringify({
          query,
          options: {
            ask,
            dry_run: dryRun,
            force_archive: forceArchive,
            verbose
          },
        }),
      });

      router.push(`/jobs/${job.job_id}`);
    } catch (err) {
      console.error(err);
      alert("Failed to start job");
      setLoading(false);
    }
  }

  return (
    <section className="flex flex-col gap-12 animate-in fade-in duration-500 slide-in-from-bottom-4">
      {/* Hero */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-br from-white to-white/60 bg-clip-text text-transparent">
          Download Music <br className="hidden sm:block" />
          <span className="text-primary">Effortlessly</span>
        </h1>
        <p className="text-muted-foreground text-lg max-w-md mx-auto">
          Search for any song, album, or artist. TrueTrack handles the metadata, artwork, and organization globally.
        </p>
      </div>

      {/* Main Input */}
      <div className="w-full max-w-xl mx-auto space-y-4">
        <div className="relative group">
          <div className="absolute inset-0 bg-primary/20 rounded-xl blur-xl group-hover:bg-primary/30 transition-all duration-500 opacity-0 group-hover:opacity-100" />
          <div className="relative flex items-center bg-surface/80 border border-zinc-800 rounded-xl p-2 focus-within:ring-2 focus-within:ring-primary/50 focus-within:border-primary/50 transition-all shadow-xl">
            <input
              className="flex-1 bg-transparent border-none text-lg px-4 py-3 placeholder:text-zinc-600 focus:outline-none focus:ring-0"
              placeholder="Search for a song..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") submit();
              }}
              autoFocus
            />
            <button
              onClick={submit}
              disabled={loading || !query.trim()}
              className="group p-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:hover:bg-primary transition-all cursor-pointer shadow-lg shadow-primary/20 hover:shadow-primary/40 hover:scale-[1.02]"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
              ) : (
                <ArrowRight size={20} className="transition-transform duration-300 group-hover:translate-x-1" />
              )}
            </button>
          </div>
        </div>

        {/* Options Toggle */}
        <div className="flex justify-center">
          <button
            onClick={() => setShowOptions(!showOptions)}
            className="text-xs font-medium text-muted-foreground hover:text-foreground flex items-center gap-1.5 px-3 py-1.5 rounded-full hover:bg-zinc-800/50 transition-colors"
          >
            <Settings2 size={12} />
            {showOptions ? "Hide Options" : "Advanced Options"}
          </button>
        </div>

        {/* Advanced Options Panel */}
        {showOptions && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4 bg-zinc-900/30 border border-zinc-800/50 rounded-xl animate-in zoom-in-95 duration-200">
            <OptionToggle
              label="Interactive Mode"
              description="Ask before choosing source/metadata"
              active={ask}
              onChange={setAsk}
              icon={Sparkles}
            />
            <OptionToggle
              label="Dry Run"
              description="Simulate without downloading"
              active={dryRun}
              onChange={setDryRun}
              icon={CloudDownload}
            />
            <OptionToggle
              label="Force Archive"
              description="Skip metadata matching"
              active={forceArchive}
              onChange={setForceArchive}
              icon={Archive}
            />
            <OptionToggle
              label="Verbose Logging"
              description="Show detailed pipeline logs"
              active={verbose}
              onChange={setVerbose}
              icon={Terminal}
            />
          </div>
        )}
      </div>

      {/* Recent History */}
      {recentJobs.length > 0 && (
        <div className="w-full max-w-xl mx-auto space-y-3">
          <h3 className="text-sm font-medium text-muted-foreground px-1">Recent Downloads</h3>
          <div className="grid gap-2">
            {recentJobs.map((job) => (
              <Link
                key={job.job_id}
                href={`/jobs/${job.job_id}`}
                className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/40 border border-zinc-800 hover:bg-zinc-900 hover:border-zinc-700 transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "w-2 h-2 rounded-full",
                    job.status === 'success' ? "bg-secondary" :
                      job.status === 'error' ? "bg-destructive" :
                        job.status === 'running' ? "bg-primary animate-pulse" :
                          "bg-zinc-500"
                  )} />
                  <div className="flex flex-col">
                    <span className="font-medium text-sm text-foreground group-hover:text-primary transition-colors">
                      {job.title || job.query || "Unknown Track"}
                    </span>
                    <span className="text-xs text-muted-foreground/70">
                      {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                    </span>
                  </div>
                </div>
                <ArrowRight size={14} className="text-zinc-600 group-hover:text-zinc-400 -translate-x-2 opacity-0 group-hover:translate-x-0 group-hover:opacity-100 transition-all" />
              </Link>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function OptionToggle({ active, onChange, label, description, icon: Icon }: any) {
  return (
    <button
      onClick={() => onChange(!active)}
      className={cn(
        "flex items-start gap-3 p-3 rounded-lg text-left transition-all border",
        active
          ? "bg-primary/10 border-primary/20 bg-gradient-to-b from-primary/5 to-transparent shadow-[0_0_15px_-3px_rgba(var(--primary),0.1)]"
          : "bg-transparent border-transparent hover:bg-zinc-800/50"
      )}
    >
      <div className={cn(
        "mt-0.5 p-1 rounded",
        active ? "text-primary" : "text-zinc-500"
      )}>
        <Icon size={16} />
      </div>
      <div>
        <div className={cn(
          "text-sm font-medium",
          active ? "text-primary" : "text-zinc-400"
        )}>{label}</div>
        <div className="text-xs text-zinc-500 leading-tight mt-0.5">{description}</div>
      </div>
    </button>
  )
}
