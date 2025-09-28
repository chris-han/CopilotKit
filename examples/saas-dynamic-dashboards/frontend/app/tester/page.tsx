import type { Metadata } from "next"

import { DashboardShell } from "@/components/dashboard-shell"
import { TesterDashboard } from "@/components/tester-dashboard"

export const metadata: Metadata = {
  title: "Tester Dashboard | EnterpriseX",
}

export default function TesterPage() {
  return (
    <DashboardShell>
      <TesterDashboard />
    </DashboardShell>
  )
}
