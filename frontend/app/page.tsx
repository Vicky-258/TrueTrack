"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ArrowRight, Settings2, CloudDownload, Terminal, Archive, Sparkles, Search } from "lucide-react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { StateBadge } from "@/components/ui/StateBadge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

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
    <div className="max-w-2xl mx-auto space-y-12 pt-16">

      {/* Intro / Search Section */}
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">New Ingestion</h1>
          <p className="text-sm text-muted-foreground mt-1">Start a new pipeline job from a URL or search query.</p>
        </div>

        <div className="relative group">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors group-focus-within:text-primary" size={18} />
          <Input
            className="pl-10 h-12 text-base shadow-sm border-muted-foreground/20 focus-visible:ring-primary"
            placeholder="Enter URL or search query..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
            autoFocus
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2">
            <Button
              onClick={submit}
              disabled={loading || !query.trim()}
              size="sm"
              className="h-8 w-8 p-0 rounded-md"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
              ) : (
                <ArrowRight size={16} />
              )}
            </Button>
          </div>
        </div>

        {/* Options Toggle */}
        <div className="space-y-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowOptions(!showOptions)}
            className="text-xs text-muted-foreground hover:text-foreground h-auto py-1 px-2 -ml-2"
          >
            <Settings2 size={12} className="mr-1.5" />
            {showOptions ? "Hide Options" : "Show Options"}
          </Button>

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
        <div className="space-y-4 pt-8 border-t border-border">
          <h2 className="text-sm font-medium text-muted-foreground">Recent Activity</h2>
          <div className="space-y-2">
            {recentJobs.map((job) => (
              <Card key={job.job_id} className="group hover:border-primary/20 transition-colors">
                <Link href={`/jobs/${job.job_id}`}>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="flex flex-col gap-1 overflow-hidden">
                      <span className="font-medium text-sm text-foreground group-hover:text-primary transition-colors truncate">
                        {job.title || job.query || "Unknown Track"}
                      </span>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span>ID: {job.job_id.substring(0, 8)}</span>
                        <span>•</span>
                        <span>{formatDistanceToNow(new Date(job.created_at || new Date()), { addSuffix: true })}</span>
                      </div>
                    </div>
                    <div className="ml-4 shrink-0">
                      <StateBadge state={job.state || job.status} />
                    </div>
                  </CardContent>
                </Link>
              </Card>
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
        "flex items-center gap-3 p-3 rounded-lg text-left transition-all duration-200 border text-sm",
        active
          ? "bg-primary/10 border-primary/20 text-primary"
          : "bg-transparent border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground"
      )}
    >
      <Icon size={16} />
      <span>{label}</span>
    </button>
  )
}
