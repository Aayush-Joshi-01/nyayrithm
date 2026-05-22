"use client"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Scale } from "lucide-react"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const schema = z.object({
  title: z.string().min(2, "Title must be at least 2 characters"),
  description: z.string().optional(),
  country: z.string().min(2, "Country is required"),
  jurisdiction: z.string().optional(),
  legal_system: z.enum(["common_law", "civil_law", "sharia", "hybrid"]),
})

type FormValues = z.infer<typeof schema>

interface Props {
  open: boolean
  onClose: () => void
  onSubmit: (data: FormValues) => void
  loading?: boolean
}

export function CaseCreateModal({ open, onClose, onSubmit, loading }: Props) {
  const { register, handleSubmit, setValue, watch, formState: { errors }, reset } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { legal_system: "common_law" },
  })

  const legalSystem = watch("legal_system")

  const handleClose = () => {
    reset()
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
              <Scale className="w-4 h-4 text-amber-400" />
            </div>
            <DialogTitle>New Case</DialogTitle>
          </div>
          <DialogDescription>
            Create a legal case to organise evidence and run courtroom simulations.
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={handleSubmit((d) => { onSubmit(d); reset() })}
          className="space-y-4 mt-2"
        >
          <div className="space-y-1.5">
            <Label htmlFor="title">Case Title *</Label>
            <Input
              id="title"
              {...register("title")}
              placeholder="e.g., State vs. Kumar — 2024"
            />
            {errors.title && <p className="text-red-400 text-xs">{errors.title.message}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              {...register("description")}
              rows={3}
              placeholder="Brief case summary..."
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="country">Country *</Label>
              <Input
                id="country"
                {...register("country")}
                placeholder="India"
              />
              {errors.country && <p className="text-red-400 text-xs">{errors.country.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="jurisdiction">Jurisdiction</Label>
              <Input
                id="jurisdiction"
                {...register("jurisdiction")}
                placeholder="IN-MH"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Legal System</Label>
            <Select
              value={legalSystem}
              onValueChange={(v) => setValue("legal_system", v as FormValues["legal_system"])}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="common_law">Common Law</SelectItem>
                <SelectItem value="civil_law">Civil Law</SelectItem>
                <SelectItem value="sharia">Sharia</SelectItem>
                <SelectItem value="hybrid">Hybrid</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <DialogFooter className="mt-2">
            <Button type="button" variant="ghost" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" variant="amber" disabled={loading}>
              {loading ? "Creating…" : "Create Case"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
