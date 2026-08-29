"use client";

import { use } from "react";
import { EvidenceManager } from "@/components/evidence/EvidenceManager";
import { PageScroll } from "@/components/layout/PageScroll";

export default function EvidencePage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  return (
    <PageScroll>
      <EvidenceManager caseId={caseId} />
    </PageScroll>
  );
}
