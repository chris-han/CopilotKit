import type { Metadata } from "next"

import { DashboardShell } from "@/components/dashboard-shell"
import { DeveloperDashboard } from "@/components/developer-dashboard"

export const metadata: Metadata = {
  title: "Developer Dashboard | EnterpriseX",
}

export default function Home() {
  return (
    <DashboardShell>
      <DeveloperDashboard />
    </DashboardShell>
  )
}
