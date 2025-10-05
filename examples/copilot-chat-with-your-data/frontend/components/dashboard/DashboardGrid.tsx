"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { DashboardCard } from "./DashboardCard";
import { Dashboard } from "@/types/dashboard";
import {
  Plus,
  Search,
  LayoutDashboard,
} from "lucide-react";

interface DashboardGridProps {
  dashboards: Dashboard[];
  loading?: boolean;
  error?: string | null;
  onCreateDashboard: () => void;
  onDeleteDashboard: (dashboard: Dashboard) => void;
  onBrowseTemplates?: () => void;
  showSearch?: boolean;
  showBrowseTemplates?: boolean;
}

export function DashboardGrid({
  dashboards,
  loading = false,
  error = null,
  onCreateDashboard,
  onDeleteDashboard,
  onBrowseTemplates,
  showSearch = false,
  showBrowseTemplates = false,
}: DashboardGridProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [dashboardToDelete, setDashboardToDelete] = useState<Dashboard | null>(null);

  const filteredDashboards = showSearch
    ? dashboards.filter(dashboard =>
        dashboard.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (dashboard.description || "").toLowerCase().includes(searchQuery.toLowerCase())
      )
    : dashboards;

  const handleDeleteDashboard = (dashboard: Dashboard) => {
    setDashboardToDelete(dashboard);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteDashboard = async () => {
    if (!dashboardToDelete) return;

    try {
      onDeleteDashboard(dashboardToDelete);
      setDeleteDialogOpen(false);
      setDashboardToDelete(null);
    } catch (err) {
      console.error("Failed to delete dashboard:", err);
    }
  };

  const cancelDeleteDashboard = () => {
    setDeleteDialogOpen(false);
    setDashboardToDelete(null);
  };

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">My Dashboards</h2>
          <p className="text-sm text-muted-foreground">
            {dashboards.length} dashboard{dashboards.length !== 1 ? "s" : ""} created
          </p>
        </div>
        <Button onClick={onCreateDashboard}>
          <Plus className="mr-2 h-4 w-4" />
          New Dashboard
        </Button>
      </div>

      {/* Search */}
      {showSearch && (
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
      )}

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
                <Button onClick={onCreateDashboard}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Dashboard
                </Button>
                {showBrowseTemplates && onBrowseTemplates && (
                  <Button variant="outline" onClick={onBrowseTemplates}>
                    Browse Templates
                  </Button>
                )}
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
              showActions={true}
            />
          ))}
        </div>
      )}

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