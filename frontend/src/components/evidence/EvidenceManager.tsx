"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, FileText, Film, Mic, Image as ImageIcon, RefreshCw, Loader2, Trash2 } from "lucide-react";
import { evidenceApi } from "@/lib/api";
import { cn, formatBytes } from "@/lib/utils";
import type { Evidence } from "@/types/api";

const MODALITY_ICONS: Record<string, React.ElementType> = {
  text: FileText,
  audio: Mic,
  video: Film,
  image: ImageIcon,
  multimodal: FileText,
};

const STATUS_STYLES: Record<string, string> = {
  pending: "text-foreground/40 bg-bone/[0.05]",
  processing: "text-brass-text bg-brass/12",
  indexed: "text-role-witness bg-role-witness/12",
  error: "text-oxblood-bright bg-oxblood-bright/12",
};

export function EvidenceManager({ caseId }: { caseId: string }) {
  const qc = useQueryClient();
  const [uploading, setUploading] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["evidence", caseId],
    queryFn: () => evidenceApi.list(caseId),
    refetchInterval: 5000,
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
      for (const file of files) await evidenceApi.upload(caseId, file, file.name);
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
    <div className="mx-auto max-w-4xl space-y-7">
      <div>
        <h1 className="font-serif text-2xl font-medium tracking-tight text-bone">Evidence</h1>
        <p className="mt-1 text-[0.88rem] text-foreground/45">
          Enter documents, audio, video, and images. Each is transcribed, chunked, and indexed on
          entry.
        </p>
      </div>

      <div
        {...getRootProps()}
        className={cn(
          "cursor-pointer rounded-lg border border-dashed p-10 text-center transition-colors",
          isDragActive ? "border-brass bg-brass/[0.06]" : "border-border hover:border-brass/50 hover:bg-accent/20"
        )}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-7 w-7 animate-spin text-brass-text" />
            <p className="text-[0.85rem] text-foreground/50">Entering into evidence</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="h-7 w-7 text-foreground/35" strokeWidth={1.5} />
            <p className="font-serif text-[0.95rem] text-foreground/80">
              {isDragActive ? "Drop to enter it" : "Drop files, or click to choose"}
            </p>
            <p className="font-mono text-[0.68rem] uppercase tracking-wide text-foreground/30">
              PDF · DOCX · MP3 · MP4 · JPG · PNG · TXT
            </p>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg border border-hairline bg-bone/[0.04]" />
          ))}
        </div>
      ) : (
        <div className="divide-y divide-hairline border-y border-hairline">
          {data?.items.map((ev: Evidence) => {
            const Icon = MODALITY_ICONS[ev.modality] ?? FileText;
            return (
              <div key={ev.id} className="flex items-center gap-4 py-3">
                <Icon className="h-4 w-4 flex-shrink-0 text-foreground/35" strokeWidth={1.5} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[0.88rem] font-medium text-foreground/85">{ev.title}</p>
                  <p className="mt-0.5 font-mono text-[0.68rem] text-foreground/30 tabular">
                    {formatBytes(ev.file_size)}
                    {ev.chunk_count > 0 && ` / ${ev.chunk_count} chunks`}
                  </p>
                </div>
                <span className={cn("rounded-sm px-1.5 py-0.5 font-mono text-[0.62rem] uppercase tracking-wide", STATUS_STYLES[ev.status])}>
                  {ev.status}
                </span>
                {(ev.status === "error" || ev.status === "indexed") && (
                  <button
                    onClick={() => reindexMutation.mutate(ev.id)}
                    disabled={reindexMutation.isPending}
                    title="Re-ingest with the current embedder"
                    className="text-foreground/25 transition-colors hover:text-foreground/60"
                  >
                    <RefreshCw className="h-3.5 w-3.5" strokeWidth={1.75} />
                  </button>
                )}
                <button
                  onClick={() => { if (confirm(`Remove "${ev.title}" and de-index it?`)) deleteMutation.mutate(ev.id); }}
                  disabled={deleteMutation.isPending}
                  title="Remove and de-index"
                  className="text-foreground/25 transition-colors hover:text-oxblood-bright"
                >
                  <Trash2 className="h-3.5 w-3.5" strokeWidth={1.75} />
                </button>
              </div>
            );
          })}
          {data?.items.length === 0 && (
            <p className="py-10 text-center text-[0.85rem] text-foreground/30">Nothing entered into evidence yet.</p>
          )}
        </div>
      )}
    </div>
  );
}
