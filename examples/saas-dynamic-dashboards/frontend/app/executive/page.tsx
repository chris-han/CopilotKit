import type { Metadata } from "next"

import { DashboardShell } from "@/components/dashboard-shell"
import { PlaceholderDashboard } from "@/components/placeholder-dashboard"

export const metadata: Metadata = {
  title: "Executive Dashboard | EnterpriseX",
}

export default function ExecutivePage() {
  return (
    <DashboardShell>
      <PlaceholderDashboard title="Executive Dashboard" />
    </DashboardShell>
  )
}
