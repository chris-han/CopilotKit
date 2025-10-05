"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { DashboardViewEdit } from "@/components/dashboard/DashboardViewEdit";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Edit, Eye, ArrowLeft } from "lucide-react";
import { Dashboard } from "@/types/dashboard";
import { useDashboardContext } from "@/contexts/DashboardContext";
import { useAgUiAgent } from "@/components/ag-ui/AgUiProvider";
import Link from "next/link";

export default function DashboardPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const dashboardId = params.id as string;
  const initialMode = searchParams.get("mode") === "edit" ? "edit" : "view";

  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"view" | "edit">(initialMode);

  // Use dashboard context and AgUI for messaging
  const { setDashboard: setContextDashboard, setMode: setContextMode, setOnDashboardChange, setActiveSection } = useDashboardContext();
  const { sendMessage } = useAgUiAgent();

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch(`/api/dashboards/${dashboardId}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch dashboard: ${response.statusText}`);
        }
        const data = await response.json();
        setDashboard(data);
        // Update dashboard context
        setContextDashboard(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    };

    if (dashboardId) {
      fetchDashboard();
    }
  }, [dashboardId, setContextDashboard]);

  // Update context when mode changes
  useEffect(() => {
    setContextMode(mode);
  }, [mode, setContextMode]);

  // Update context when dashboard changes
  useEffect(() => {
    if (dashboard) {
      setContextDashboard(dashboard);
    }
  }, [dashboard, setContextDashboard]);

  const handleSave = useCallback(async (updatedConfig: any) => {
    if (!dashboard) return;

    try {
      const response = await fetch(`/api/dashboards/${dashboardId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: updatedConfig.name,
          description: updatedConfig.description,
          layout_config: updatedConfig.layout_config,
          metadata: updatedConfig.metadata,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to save dashboard");
      }

      const updatedDashboard = await response.json();
      setDashboard(updatedDashboard);
    } catch (err) {
      console.error("Failed to save dashboard:", err);
      throw err; // Re-throw so the component can handle it
    }
  }, [dashboard, dashboardId]);

  // Set up dashboard change handler for context
  useEffect(() => {
    setOnDashboardChange((updatedDashboard: Dashboard) => {
      setDashboard(updatedDashboard);
      handleSave({
        name: updatedDashboard.name,
        description: updatedDashboard.description,
        layout_config: updatedDashboard.layout_config,
        metadata: updatedDashboard.metadata,
      }).catch(console.error);
    });
  }, [setOnDashboardChange, handleSave]);

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="space-y-4">
          <div className="h-8 w-64 animate-pulse rounded bg-muted" />
          <div className="h-4 w-96 animate-pulse rounded bg-muted" />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-64 animate-pulse rounded bg-muted" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-8">
        <Card>
          <CardContent className="py-8 text-center">
            <h2 className="text-lg font-semibold text-destructive">Error Loading Dashboard</h2>
            <p className="mt-2 text-muted-foreground">{error}</p>
            <Button asChild className="mt-4">
              <Link href="/dashboards">Back to Dashboards</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="container mx-auto py-8">
        <Card>
          <CardContent className="py-8 text-center">
            <h2 className="text-lg font-semibold">Dashboard Not Found</h2>
            <p className="mt-2 text-muted-foreground">The requested dashboard could not be found.</p>
            <Button asChild className="mt-4">
              <Link href="/dashboards">Back to Dashboards</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/dashboards">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
          </Button>
          <div>
            <h1
              className={`text-2xl font-bold ${mode === "edit" ? "cursor-pointer hover:text-primary transition-colors" : ""}`}
              onClick={mode === "edit" ? () => {
                // Send AgUI message for protocol compliance
                sendMessage("Show dashboard properties editor in Data Assistant");
                // Update context for immediate UI response
                setActiveSection("dashboard-title");
              } : undefined}
              title={mode === "edit" ? "Click to edit dashboard properties in Data Assistant" : undefined}
            >
              {dashboard.name}
            </h1>
            {dashboard.description && (
              <p className="text-muted-foreground">{dashboard.description}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={mode === "view" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode("view")}
          >
            <Eye className="mr-2 h-4 w-4" />
            View
          </Button>
          <Button
            variant={mode === "edit" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode("edit")}
          >
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
        </div>
      </div>

      <DashboardViewEdit
        dashboard={dashboard}
        mode={mode}
        onSave={handleSave}
      />
    </div>
  );
}