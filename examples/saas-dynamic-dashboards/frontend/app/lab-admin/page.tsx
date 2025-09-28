import type { Metadata } from "next"

import { DashboardShell } from "@/components/dashboard-shell"
import { PlaceholderDashboard } from "@/components/placeholder-dashboard"

export const metadata: Metadata = {
  title: "Lab Admin Dashboard | EnterpriseX",
}

export default function LabAdminPage() {
  return (
    <DashboardShell>
      <PlaceholderDashboard title="Lab Admin Dashboard" />
    </DashboardShell>
  )
}
