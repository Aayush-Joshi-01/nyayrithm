"use client";

import { CaseDashboard } from "@/components/case/CaseDashboard";
import { PageScroll } from "@/components/layout/PageScroll";

export default function DashboardPage() {
  return (
    <PageScroll>
      <CaseDashboard />
    </PageScroll>
  );
}
