"use client";

import { use } from "react";
import { EvidenceManager } from "@/components/evidence/EvidenceManager";

export default function EvidencePage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  return <EvidenceManager caseId={caseId} />;
}
