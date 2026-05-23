"use client";

import { use } from "react";
import { SimulationShell } from "@/components/simulation/SimulationShell";

export default function SimulationPage({
  params,
}: {
  params: Promise<{ caseId: string; simId: string }>;
}) {
  const { caseId, simId } = use(params);
  return <SimulationShell caseId={caseId} simId={simId} />;
}
