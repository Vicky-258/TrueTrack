import Link from "next/link";
import "./globals.css";
import { cn } from "@/lib/utils";
import { History, Disc3 } from "lucide-react";

export const metadata = {
  title: "TrueTrack",
  description: "Effortless music downloader",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-foreground min-h-screen flex flex-col antialiased selection:bg-blue-500/30 selection:text-blue-200">
        <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/60 backdrop-blur-md supports-[backdrop-filter]:bg-background/60">
          <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
            <Link
              href="/"
              className="flex items-center gap-2 font-bold text-lg tracking-tight hover:opacity-80 transition-opacity"
            >
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white">
                <Disc3 size={18} className="animate-spin-slow" />
              </div>
              TrueTrack
            </Link>

            <nav className="flex items-center gap-6 text-sm font-medium">
              <Link
                href="/"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                New Download
              </Link>
              <Link
                href="/jobs"
                className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <History size={16} />
                History
              </Link>
            </nav>
          </div>
        </header>

        <main className="flex-1 w-full max-w-3xl mx-auto px-6 pt-32 pb-20">
          {children}
        </main>
      </body>
    </html>
  );
}
