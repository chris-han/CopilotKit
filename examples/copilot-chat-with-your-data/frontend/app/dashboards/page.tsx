"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { DashboardTemplateGallery } from "@/components/dashboard/DashboardTemplateGallery";
import {
  Plus,
  Search,
  Calendar,
  MoreHorizontal,
  Edit,
  Eye,
  Trash2,
  LayoutDashboard,
} from "lucide-react";

interface Dashboard {
  id: string;
  name: string;
  description?: string;
  layout_config: any;
  metadata: any;
  is_public: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface DashboardTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  thumbnail_url?: string;
  layout_config: any;
  default_data: any;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
}

export default function DashboardsPage() {
  const router = useRouter();
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("my-dashboards");

  // Delete confirmation dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [dashboardToDelete, setDashboardToDelete] = useState<Dashboard | null>(null);

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

  const filteredDashboards = dashboards.filter(dashboard =>
    dashboard.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (dashboard.description || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

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

  const handleDeleteDashboard = (dashboard: Dashboard) => {
    setDashboardToDelete(dashboard);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteDashboard = async () => {
    if (!dashboardToDelete) return;

    try {
      const response = await fetch(`/api/dashboards/${dashboardToDelete.id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete dashboard");
      }

      setDashboards(dashboards.filter(d => d.id !== dashboardToDelete.id));
      setDeleteDialogOpen(false);
      setDashboardToDelete(null);
    } catch (err) {
      console.error("Failed to delete dashboard:", err);
      // Could add error state here if needed
    }
  };

  const cancelDeleteDashboard = () => {
    setDeleteDialogOpen(false);
    setDashboardToDelete(null);
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
          <Button onClick={createBlankDashboard}>
            <Plus className="mr-2 h-4 w-4" />
            New Dashboard
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
          <TabsTrigger value="my-dashboards">My Dashboards</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
        </TabsList>

        <TabsContent value="my-dashboards" className="space-y-6">
          {/* Search */}
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search dashboards..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          {/* Dashboard Grid */}
          {loading ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <div className="h-4 w-3/4 animate-pulse rounded bg-muted" />
                    <div className="h-3 w-full animate-pulse rounded bg-muted" />
                  </CardHeader>
                  <CardContent>
                    <div className="h-32 animate-pulse rounded bg-muted" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : error ? (
            <Card>
              <CardContent className="py-8 text-center">
                <h3 className="text-lg font-semibold text-destructive">Error Loading Dashboards</h3>
                <p className="mt-2 text-muted-foreground">{error}</p>
              </CardContent>
            </Card>
          ) : filteredDashboards.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <LayoutDashboard className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-4 text-lg font-semibold">No dashboards found</h3>
                <p className="mt-2 text-muted-foreground">
                  {searchQuery ? "Try adjusting your search criteria" : "Create your first dashboard to get started"}
                </p>
                {!searchQuery && (
                  <div className="mt-4 flex gap-2 justify-center">
                    <Button onClick={createBlankDashboard}>
                      <Plus className="mr-2 h-4 w-4" />
                      Create Dashboard
                    </Button>
                    <Button variant="outline" onClick={() => setActiveTab("templates")}>
                      Browse Templates
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredDashboards.map((dashboard) => (
                <DashboardCard
                  key={dashboard.id}
                  dashboard={dashboard}
                  onDelete={handleDeleteDashboard}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="templates" className="space-y-6">
          <DashboardTemplateGallery onCreateFromTemplate={handleCreateFromTemplate} />
        </TabsContent>
      </Tabs>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Dashboard</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{dashboardToDelete?.name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={cancelDeleteDashboard}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDeleteDashboard}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface DashboardCardProps {
  dashboard: Dashboard;
  onDelete: (dashboard: Dashboard) => void;
}

function DashboardCard({ dashboard, onDelete }: DashboardCardProps) {
  const itemCount = dashboard.layout_config?.items?.length || 0;

  return (
    <Card className="group relative transition-all hover:shadow-lg">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base truncate">{dashboard.name}</CardTitle>
            {dashboard.description && (
              <CardDescription className="text-sm line-clamp-2">
                {dashboard.description}
              </CardDescription>
            )}
          </div>
          {dashboard.is_public && (
            <Badge variant="secondary" className="ml-2">
              Public
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {/* Dashboard Preview */}
        <div className="mb-4 rounded border bg-muted/30 p-3">
          <div className="grid grid-cols-4 gap-1">
            {Array.from({ length: Math.min(itemCount, 8) }).map((_, index) => (
              <div
                key={index}
                className="flex h-4 items-center justify-center rounded bg-background/60"
              >
                <div className="h-2 w-2 rounded bg-muted-foreground/40" />
              </div>
            ))}
            {itemCount === 0 && (
              <div className="col-span-4 flex h-8 items-center justify-center text-xs text-muted-foreground">
                Empty dashboard
              </div>
            )}
          </div>
        </div>

        {/* Dashboard Info */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{itemCount} components</span>
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {new Date(dashboard.updated_at).toLocaleDateString()}
            </span>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button asChild variant="outline" size="sm" className="flex-1">
              <Link href={`/dashboard/${dashboard.id}`}>
                <Eye className="mr-2 h-4 w-4" />
                View
              </Link>
            </Button>
            <Button asChild size="sm" className="flex-1">
              <Link href={`/dashboard/${dashboard.id}?mode=edit`}>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Link>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDelete(dashboard)}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}