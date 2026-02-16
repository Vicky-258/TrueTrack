"use client";

import { useState, useEffect } from "react";
import { Settings, Save, FolderOpen, AlertCircle, CheckCircle2 } from "lucide-react";
import { useSettings, updateMusicLibraryPath } from "@/hooks/useSettings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
    const { settings, isLoading, mutate } = useSettings();
    const [path, setPath] = useState("");
    const [saving, setSaving] = useState(false);
    const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    useEffect(() => {
        if (settings) {
            setPath(settings.music_library_path);
        }
    }, [settings]);

    const handleSave = async () => {
        setSaving(true);
        setStatus(null);
        try {
            await updateMusicLibraryPath(path);
            await mutate();
            setStatus({ type: 'success', message: 'Settings saved successfully' });

            // Clear success message after 3 seconds
            setTimeout(() => setStatus(null), 3000);
        } catch (err: any) {
            setStatus({ type: 'error', message: err.message || 'Failed to save settings' });
        } finally {
            setSaving(false);
        }
    };

    if (isLoading) {
        return <div className="p-8 text-muted-foreground">Loading settings...</div>;
    }

    return (
        <div className="space-y-8 max-w-2xl animate-in fade-in duration-500">
            <div className="flex items-center gap-2 border-b border-border pb-6">
                <div className="p-2 bg-muted/20 rounded-lg text-muted-foreground">
                    <Settings size={20} />
                </div>
                <div>
                    <h1 className="text-2xl font-semibold tracking-tight text-foreground">Settings</h1>
                    <p className="text-sm text-muted-foreground">Manage your application configuration</p>
                </div>
            </div>

            <div className="space-y-6">
                {/* Music Library Section */}
                <Card>
                    <CardHeader>
                        <div className="flex items-start justify-between">
                            <div className="space-y-1">
                                <CardTitle className="flex items-center gap-2 text-base">
                                    <FolderOpen size={18} className="text-muted-foreground" />
                                    Music Library
                                </CardTitle>
                                <CardDescription>
                                    Where your music files are stored and managed.
                                </CardDescription>
                            </div>
                            {settings?.source === 'env' && (
                                <span className="px-2 py-1 rounded bg-muted text-xs text-muted-foreground border border-border font-mono">
                                    ENV LOCKED
                                </span>
                            )}
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-3">
                            <label className="text-sm font-medium text-muted-foreground">Root Directory Path</label>
                            <Input
                                value={path}
                                onChange={(e) => setPath(e.target.value)}
                                disabled={settings?.source === 'env'}
                                placeholder="/path/to/music/library"
                                className={cn(
                                    settings?.source === 'env' && "opacity-60 cursor-not-allowed bg-muted"
                                )}
                            />

                            {settings?.source !== 'env' && (
                                <div className="flex items-center justify-between pt-2">
                                    {status ? (
                                        <div className={cn(
                                            "text-sm flex items-center gap-2",
                                            status.type === 'success' ? "text-emerald-500" : "text-destructive"
                                        )}>
                                            {status.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                                            {status.message}
                                        </div>
                                    ) : (
                                        <div />
                                    )}

                                    <Button
                                        onClick={handleSave}
                                        disabled={saving || path === settings?.music_library_path}
                                    >
                                        {saving ? (
                                            <>
                                                <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin mr-2" />
                                                Saving...
                                            </>
                                        ) : (
                                            <>
                                                <Save size={16} className="mr-2 opacity-70" />
                                                Save Changes
                                            </>
                                        )}
                                    </Button>
                                </div>
                            )}

                            {settings?.source === 'env' && (
                                <p className="text-xs text-amber-500/80 mt-2 flex items-center gap-1.5">
                                    <AlertCircle size={12} />
                                    This setting is currently managed by environment variables.
                                </p>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Appearance Section */}
                <Card className="opacity-75">
                    <CardContent className="p-6 flex items-center justify-between">
                        <div className="space-y-0.5">
                            <h3 className="font-medium text-foreground">Dark Mode</h3>
                            <p className="text-xs text-muted-foreground">Always enabled for eye comfort</p>
                        </div>
                        <div className="h-6 w-10 rounded-full bg-primary/20 border border-primary/50 relative cursor-not-allowed">
                            <div className="absolute right-1 top-1 h-3.5 w-3.5 rounded-full bg-primary" />
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
