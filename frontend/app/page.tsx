"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function Home() {
  const [query, setQuery] = useState("");
  const [ask, setAsk] = useState(true);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function submit() {
    if (!query.trim()) return;

    setLoading(true);

    try {
      const job = await api<any>("/jobs", {
        method: "POST",
        body: JSON.stringify({
          query,
          options: { ask },
        }),
      });

      router.push(`/jobs/${job.job_id}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-6">
      {/* Page title */}
      <header>
        <h1 className="text-xl font-semibold">New Download</h1>
        <p className="text-sm text-zinc-400">
          Search for a song and let TrueTrack handle the rest.
        </p>
      </header>

      {/* Search input */}
      <input
        className="w-full p-3 rounded bg-zinc-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
        placeholder="Song name / artist"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") submit();
        }}
      />

      {/* Ask toggle */}
      <label className="flex items-center gap-2 text-sm text-zinc-400">
        <input
          type="checkbox"
          checked={ask}
          onChange={(e) => setAsk(e.target.checked)}
        />
        Ask before choosing source / metadata
      </label>

      {/* Action */}
      <button
        onClick={submit}
        disabled={loading}
        className="w-full p-3 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50"
      >
        {loading ? "Starting…" : "Start Download"}
      </button>
    </section>
  );
}
