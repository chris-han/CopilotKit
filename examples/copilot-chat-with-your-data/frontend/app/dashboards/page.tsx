"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DashboardTemplateGallery } from "@/components/dashboard/DashboardTemplateGallery";
import { DashboardGrid } from "@/components/dashboard/DashboardGrid";
import { Dashboard } from "@/types/dashboard";

interface DashboardTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  thumbnail_url?: string;
  layout_config: Record<string, unknown>;
  default_data: Record<string, unknown>;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
}

export default function DashboardsPage() {
  const router = useRouter();
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("my-dashboards");

  useEffect(() => {
    const fetchDashboards = async () => {
      try {
        const response = await fetch("/api/dashboards");
        if (!response.ok) {
          throw new Error("Failed to fetch dashboards");
        }
        const data = await response.json();
        setDashboards(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboards");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboards();
  }, []);

  const handleCreateFromTemplate = async (template: DashboardTemplate, dashboardName: string, description?: string) => {
    try {
      const response = await fetch("/api/dashboards", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: dashboardName,
          description: description || undefined,
          layout_config: template.layout_config,
          metadata: { template_id: template.id },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create dashboard");
      }

      const newDashboard = await response.json();

      // Refresh dashboards list
      const refreshResponse = await fetch("/api/dashboards");
      if (refreshResponse.ok) {
        const updatedDashboards = await refreshResponse.json();
        setDashboards(updatedDashboards);
      }

      // Navigate to the new dashboard
      router.push(`/dashboard/${newDashboard.id}?mode=edit`);
    } catch (err) {
      console.error("Failed to create dashboard:", err);
      // You could add error handling UI here
    }
  };

  const handleDeleteDashboard = async (dashboard: Dashboard) => {
    try {
      const response = await fetch(`/api/dashboards/${dashboard.id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete dashboard");
      }

      setDashboards(dashboards.filter(d => d.id !== dashboard.id));
    } catch (err) {
      console.error("Failed to delete dashboard:", err);
      // Could add error state here if needed
    }
  };

  const createBlankDashboard = async () => {
    try {
      const response = await fetch("/api/dashboards", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "New Dashboard",
          description: "A blank dashboard ready for customization",
          layout_config: {
            grid: { cols: 4, rows: "auto" },
            items: [],
          },
          metadata: {},
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create dashboard");
      }

      const newDashboard = await response.json();
      router.push(`/dashboard/${newDashboard.id}?mode=edit`);
    } catch (err) {
      console.error("Failed to create dashboard:", err);
    }
  };

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Dashboards</h1>
            <p className="text-muted-foreground">
              Create and manage your analytics dashboards
            </p>
          </div>
        </div>
      </div>

      <Card>
        <CardContent className="p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
              <TabsTrigger value="my-dashboards">My Dashboards</TabsTrigger>
              <TabsTrigger value="templates">Templates</TabsTrigger>
            </TabsList>

            <TabsContent value="my-dashboards" className="space-y-6">
              <DashboardGrid
                dashboards={dashboards}
                loading={loading}
                error={error}
                onCreateDashboard={createBlankDashboard}
                onDeleteDashboard={handleDeleteDashboard}
                onBrowseTemplates={() => setActiveTab("templates")}
                showSearch={true}
                showBrowseTemplates={true}
              />
            </TabsContent>

            <TabsContent value="templates" className="space-y-6">
              <DashboardTemplateGallery onCreateFromTemplate={handleCreateFromTemplate} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
