import Link from "next/link";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-zinc-950 text-zinc-100">
        <header className="p-4 border-b border-zinc-800 flex justify-between">
          <Link href="/" className="font-bold">
            TrueTrack
          </Link>

          <nav className="space-x-4 text-sm">
            <Link href="/" className="hover:underline">
              New Download
            </Link>
            <Link href="/jobs" className="hover:underline">
              History
            </Link>
          </nav>
        </header>

        <main className="max-w-3xl mx-auto p-6">
          {children}
        </main>
      </body>
    </html>
  );
}
