"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { DashboardViewEdit } from "@/components/dashboard/DashboardViewEdit";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Edit, Eye, ArrowLeft } from "lucide-react";
import { Dashboard } from "@/types/dashboard";
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

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch(`/api/dashboards/${dashboardId}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch dashboard: ${response.statusText}`);
        }
        const data = await response.json();
        setDashboard(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    };

    if (dashboardId) {
      fetchDashboard();
    }
  }, [dashboardId]);

  const handleSave = async (updatedConfig: any) => {
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
    }
  };

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
            <h1 className="text-2xl font-bold">{dashboard.name}</h1>
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