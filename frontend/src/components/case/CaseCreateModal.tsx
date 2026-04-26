"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { X } from "lucide-react";

const schema = z.object({
  title: z.string().min(2, "Title must be at least 2 characters"),
  description: z.string().optional(),
  country: z.string().min(2, "Country is required"),
  jurisdiction: z.string().optional(),
  legal_system: z.enum(["common_law", "civil_law", "sharia", "hybrid"]),
});

type FormValues = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: FormValues) => void;
  loading?: boolean;
}

export function CaseCreateModal({ open, onClose, onSubmit, loading }: Props) {
  const { register, handleSubmit, formState: { errors }, reset } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { legal_system: "common_law" },
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md mx-4 bg-card border border-border rounded-xl shadow-2xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold">New Case</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit((d) => { onSubmit(d); reset(); })} className="space-y-4">
          <div>
            <label className="text-sm text-muted-foreground block mb-1">Case Title *</label>
            <input
              {...register("title")}
              className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
              placeholder="e.g., State vs. Kumar — 2024"
            />
            {errors.title && <p className="text-red-400 text-xs mt-1">{errors.title.message}</p>}
          </div>

          <div>
            <label className="text-sm text-muted-foreground block mb-1">Description</label>
            <textarea
              {...register("description")}
              rows={3}
              className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500 resize-none"
              placeholder="Brief case summary..."
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm text-muted-foreground block mb-1">Country *</label>
              <input
                {...register("country")}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
                placeholder="India"
              />
              {errors.country && <p className="text-red-400 text-xs mt-1">{errors.country.message}</p>}
            </div>
            <div>
              <label className="text-sm text-muted-foreground block mb-1">Jurisdiction</label>
              <input
                {...register("jurisdiction")}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
                placeholder="IN-MH"
              />
            </div>
          </div>

          <div>
            <label className="text-sm text-muted-foreground block mb-1">Legal System</label>
            <select
              {...register("legal_system")}
              className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
            >
              <option value="common_law">Common Law</option>
              <option value="civil_law">Civil Law</option>
              <option value="sharia">Sharia</option>
              <option value="hybrid">Hybrid</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black rounded-lg text-sm font-medium transition-colors"
          >
            {loading ? "Creating..." : "Create Case"}
          </button>
        </form>
      </div>
    </div>
  );
}
