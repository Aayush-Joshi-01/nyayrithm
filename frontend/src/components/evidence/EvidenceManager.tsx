"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, FileText, Film, Mic, Image, RefreshCw, Loader2, Trash2 } from "lucide-react";
import { evidenceApi } from "@/lib/api";
import { cn, formatBytes } from "@/lib/utils";
import type { Evidence } from "@/types/api";

const MODALITY_ICONS: Record<string, React.ElementType> = {
  text: FileText,
  audio: Mic,
  video: Film,
  image: Image,
  multimodal: FileText,
};

const STATUS_STYLES: Record<string, string> = {
  pending: "text-slate-400 bg-slate-400/10",
  processing: "text-amber-400 bg-amber-400/10 animate-pulse-slow",
  indexed: "text-emerald-400 bg-emerald-400/10",
  error: "text-red-400 bg-red-400/10",
};

export function EvidenceManager({ caseId }: { caseId: string }) {
  const qc = useQueryClient();
  const [uploading, setUploading] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["evidence", caseId],
    queryFn: () => evidenceApi.list(caseId),
    refetchInterval: 5000, // poll for status updates
  });

  const reindexMutation = useMutation({
    mutationFn: (evId: string) => evidenceApi.reindex(caseId, evId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evidence", caseId] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (evId: string) => evidenceApi.delete(caseId, evId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evidence", caseId] }),
  });

  const onDrop = useCallback(async (files: File[]) => {
    setUploading(true);
    try {
      for (const file of files) {
        await evidenceApi.upload(caseId, file, file.name);
      }
      qc.invalidateQueries({ queryKey: ["evidence", caseId] });
    } finally {
      setUploading(false);
    }
  }, [caseId, qc]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "audio/*": [".mp3", ".wav", ".ogg", ".flac"],
      "video/*": [".mp4", ".mov", ".avi", ".webm"],
      "image/*": [".jpg", ".jpeg", ".png", ".tiff"],
      "text/*": [".txt", ".md"],
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">Evidence</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Upload documents, audio, video, and images for AI analysis
        </p>
      </div>

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors",
          isDragActive
            ? "border-amber-500 bg-amber-500/5"
            : "border-border hover:border-amber-500/50 hover:bg-accent/20"
        )}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 text-amber-400 animate-spin" />
            <p className="text-sm text-muted-foreground">Uploading...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="w-8 h-8 text-muted-foreground" />
            <p className="text-sm font-medium">
              {isDragActive ? "Drop files here" : "Drag & drop evidence files"}
            </p>
            <p className="text-xs text-muted-foreground">
              PDF, DOCX, MP3, MP4, JPG, PNG, TXT — all supported
            </p>
          </div>
        )}
      </div>

      {/* Evidence List */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg bg-card border border-border animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {data?.items.map((ev: Evidence) => {
            const Icon = MODALITY_ICONS[ev.modality] ?? FileText;
            return (
              <div
                key={ev.id}
                className="flex items-center gap-4 p-4 rounded-lg bg-card border border-border hover:border-border/80 transition-colors"
              >
                <div className="w-9 h-9 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                  <Icon className="w-4 h-4 text-muted-foreground" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{ev.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-muted-foreground">{formatBytes(ev.file_size)}</span>
                    {ev.chunk_count > 0 && (
                      <span className="text-xs text-muted-foreground">· {ev.chunk_count} chunks</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn("text-xs px-2 py-0.5 rounded-full", STATUS_STYLES[ev.status])}>
                    {ev.status}
                  </span>
                  {(ev.status === "error" || ev.status === "indexed") && (
                    <button
                      onClick={() => reindexMutation.mutate(ev.id)}
                      disabled={reindexMutation.isPending}
                      title="Re-index"
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <button
                    onClick={() => {
                      if (confirm(`Remove "${ev.title}"?`)) deleteMutation.mutate(ev.id);
                    }}
                    disabled={deleteMutation.isPending}
                    title="Remove evidence"
                    className="text-muted-foreground hover:text-red-400"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
          {data?.items.length === 0 && (
            <p className="text-center text-muted-foreground text-sm py-10">
              No evidence uploaded yet
            </p>
          )}
        </div>
      )}
    </div>
  );
}
