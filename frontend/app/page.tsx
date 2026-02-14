"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ArrowRight, Settings2, CloudDownload, Terminal, Archive, Sparkles, Search } from "lucide-react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { StateBadge } from "@/components/ui/StateBadge";

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
    api<any[]>("/jobs").then((jobs) => {
      setRecentJobs(jobs.slice(0, 5));
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
    <div className="max-w-2xl mx-auto space-y-12 pt-10">

      {/* Search Section */}
      <div className="space-y-6">
        <h1 className="text-xl font-semibold text-zinc-100">New Ingestion</h1>

        <div className="relative">
          <div className="flex items-center bg-zinc-900 border border-zinc-700/50 rounded-lg p-2 focus-within:ring-1 focus-within:ring-blue-500/50 focus-within:border-blue-500/50 transition-all">
            <Search className="ml-3 text-zinc-500" size={20} />
            <input
              className="flex-1 bg-transparent border-none text-base px-4 py-2 text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:ring-0"
              placeholder="Enter URL or search query..."
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
              className="px-4 py-2 rounded-md bg-zinc-100 text-zinc-900 font-medium hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-zinc-900/30 border-t-zinc-900 rounded-full animate-spin" />
              ) : (
                <ArrowRight size={18} />
              )}
            </button>
          </div>
        </div>

        {/* Options Toggle */}
        <div className="space-y-4">
          <button
            onClick={() => setShowOptions(!showOptions)}
            className="text-xs font-medium text-zinc-500 hover:text-zinc-300 flex items-center gap-1.5 transition-colors"
          >
            <Settings2 size={12} />
            {showOptions ? "Hide Options" : "Show Options"}
          </button>

          {showOptions && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 animate-in fade-in slide-in-from-top-2 duration-200">
              <OptionToggle
                label="Interactive Mode"
                active={ask}
                onChange={setAsk}
                icon={Sparkles}
              />
              <OptionToggle
                label="Dry Run"
                active={dryRun}
                onChange={setDryRun}
                icon={CloudDownload}
              />
              <OptionToggle
                label="Force Archive"
                active={forceArchive}
                onChange={setForceArchive}
                icon={Archive}
              />
              <OptionToggle
                label="Verbose Logging"
                active={verbose}
                onChange={setVerbose}
                icon={Terminal}
              />
            </div>
          )}
        </div>
      </div>

      {/* Recent History */}
      {recentJobs.length > 0 && (
        <div className="space-y-4 pt-8 border-t border-zinc-800/50">
          <h2 className="text-sm font-semibold text-zinc-400">Recent Activity</h2>
          <div className="space-y-2">
            {recentJobs.map((job) => (
              <Link
                key={job.job_id}
                href={`/jobs/${job.job_id}`}
                className="flex items-center justify-between p-3 rounded-lg border border-zinc-800/50 hover:bg-zinc-900 hover:border-zinc-700 transition-colors group"
              >
                <div className="flex flex-col gap-0.5">
                  <span className="font-medium text-sm text-zinc-200 group-hover:text-blue-400 transition-colors truncate max-w-[300px]">
                    {job.title || job.query || "Unknown Track"}
                  </span>
                  <span className="text-xs text-zinc-500">
                    {formatDistanceToNow(new Date(job.created_at || new Date()), { addSuffix: true })}
                  </span>
                </div>
                <StateBadge state={job.current_state} className="opacity-70 group-hover:opacity-100" />
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function OptionToggle({ active, onChange, label, icon: Icon }: any) {
  return (
    <button
      onClick={() => onChange(!active)}
      className={cn(
        "flex items-center gap-3 p-3 rounded-md text-left transition-all border text-sm",
        active
          ? "bg-blue-500/10 border-blue-500/20 text-blue-400"
          : "bg-zinc-900/40 border-zinc-800 text-zinc-500 hover:bg-zinc-900 hover:text-zinc-400"
      )}
    >
      <Icon size={16} />
      <span>{label}</span>
    </button>
  )
}
