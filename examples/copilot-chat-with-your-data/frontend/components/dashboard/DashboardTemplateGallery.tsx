"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  BarChart3,
  PieChart,
  LineChart,
  Activity,
  FileText,
  Star,
  Plus,
  Search,
  Filter,
} from "lucide-react";

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

interface DashboardTemplateGalleryProps {
  onCreateFromTemplate?: (template: DashboardTemplate, dashboardName: string, description?: string) => Promise<void>;
}

const CATEGORY_COLORS: Record<string, string> = {
  Financial: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
  Sales: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  Operations: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
  Executive: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300",
  Marketing: "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-300",
  Analytics: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300",
};

const getItemTypeIcon = (type: string) => {
  switch (type) {
    case "chart":
      return BarChart3;
    case "metric":
      return Activity;
    case "text":
    case "commentary":
      return FileText;
    default:
      return BarChart3;
  }
};

const getChartTypeIcon = (chartType: string) => {
  switch (chartType) {
    case "area":
      return LineChart;
    case "bar":
      return BarChart3;
    case "donut":
      return PieChart;
    default:
      return BarChart3;
  }
};

export function DashboardTemplateGallery({ onCreateFromTemplate }: DashboardTemplateGalleryProps) {
  const router = useRouter();
  const [templates, setTemplates] = useState<DashboardTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedTemplate, setSelectedTemplate] = useState<DashboardTemplate | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [dashboardName, setDashboardName] = useState("");
  const [dashboardDescription, setDashboardDescription] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await fetch("/api/dashboard-templates");
        if (!response.ok) {
          throw new Error("Failed to fetch templates");
        }
        const data = await response.json();
        setTemplates(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load templates");
      } finally {
        setLoading(false);
      }
    };

    fetchTemplates();
  }, []);

  // Early returns before any computations to avoid hook order issues
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
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
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Card>
          <CardContent className="py-8 text-center">
            <h3 className="text-lg font-semibold text-destructive">Error Loading Templates</h3>
            <p className="mt-2 text-muted-foreground">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const categories = Array.from(new Set(templates.map(t => t.category))).sort();
  const featuredTemplates = templates.filter(t => t.is_featured);

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "all" || template.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleCreateFromTemplate = async () => {
    if (!selectedTemplate || !dashboardName.trim()) return;

    setCreating(true);
    try {
      if (onCreateFromTemplate) {
        await onCreateFromTemplate(selectedTemplate, dashboardName, dashboardDescription);
      } else {
        // Default behavior: create dashboard via API and navigate
        const response = await fetch("/api/dashboards", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: dashboardName,
            description: dashboardDescription || undefined,
            layout_config: selectedTemplate.layout_config,
            metadata: { template_id: selectedTemplate.id },
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to create dashboard");
        }

        const newDashboard = await response.json();
        router.push(`/dashboard/${newDashboard.id}?mode=edit`);
      }

      setCreateDialogOpen(false);
      setDashboardName("");
      setDashboardDescription("");
      setSelectedTemplate(null);
    } catch (err) {
      console.error("Failed to create dashboard:", err);
    } finally {
      setCreating(false);
    }
  };

  const openCreateDialog = (template: DashboardTemplate) => {
    setSelectedTemplate(template);
    setDashboardName(`${template.name} Dashboard`);
    setDashboardDescription(template.description);
    setCreateDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Search and Filter */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 items-center gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-48">
              <Filter className="mr-2 h-4 w-4" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {categories.map(category => (
                <SelectItem key={category} value={category}>
                  {category}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Featured Templates */}
      {featuredTemplates.length > 0 && selectedCategory === "all" && !searchQuery && (
        <section>
          <div className="mb-4 flex items-center gap-2">
            <Star className="h-5 w-5 text-yellow-500" />
            <h2 className="text-lg font-semibold">Featured Templates</h2>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {featuredTemplates.map(template => (
              <TemplateCard
                key={template.id}
                template={template}
                onUseTemplate={openCreateDialog}
                featured
              />
            ))}
          </div>
        </section>
      )}

      {/* All Templates */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {searchQuery || selectedCategory !== "all" ? "Search Results" : "All Templates"}
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              ({filteredTemplates.length})
            </span>
          </h2>
        </div>

        {filteredTemplates.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <h3 className="text-lg font-semibold">No templates found</h3>
              <p className="mt-2 text-muted-foreground">
                Try adjusting your search or filter criteria
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredTemplates.map(template => (
              <TemplateCard
                key={template.id}
                template={template}
                onUseTemplate={openCreateDialog}
              />
            ))}
          </div>
        )}
      </section>

      {/* Create Dashboard Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Dashboard from Template</DialogTitle>
            <DialogDescription>
              {selectedTemplate && `Creating a new dashboard based on "${selectedTemplate.name}" template.`}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="dashboard-name">Dashboard Name</Label>
              <Input
                id="dashboard-name"
                value={dashboardName}
                onChange={(e) => setDashboardName(e.target.value)}
                placeholder="Enter dashboard name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="dashboard-description">Description (Optional)</Label>
              <Textarea
                id="dashboard-description"
                value={dashboardDescription}
                onChange={(e) => setDashboardDescription(e.target.value)}
                placeholder="Enter dashboard description"
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateFromTemplate}
              disabled={!dashboardName.trim() || creating}
            >
              {creating ? "Creating..." : "Create Dashboard"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface TemplateCardProps {
  template: DashboardTemplate;
  onUseTemplate: (template: DashboardTemplate) => void;
  featured?: boolean;
}

function TemplateCard({ template, onUseTemplate, featured }: TemplateCardProps) {
  const items = template.layout_config?.items || [];
  const itemTypes = Array.from(new Set(items.map((item: any) => item.type)));
  const chartTypes = Array.from(new Set(
    items
      .filter((item: any) => item.type === "chart" && item.chartType)
      .map((item: any) => item.chartType)
  ));

  return (
    <Card className="group relative transition-all hover:shadow-lg">
      {featured && (
        <Badge className="absolute -top-2 -right-2 z-10 bg-yellow-500 text-yellow-50">
          <Star className="mr-1 h-3 w-3" />
          Featured
        </Badge>
      )}

      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-base">{template.name}</CardTitle>
            <CardDescription className="text-sm">{template.description}</CardDescription>
          </div>
          <Badge className={CATEGORY_COLORS[template.category] || "bg-gray-100 text-gray-800"}>
            {template.category}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        {/* Template Preview */}
        <div className="mb-4 rounded border bg-muted/30 p-3">
          <div className="grid grid-cols-4 gap-1">
            {items.slice(0, 8).map((item: any, index: number) => {
              const Icon = item.type === "chart" && item.chartType
                ? getChartTypeIcon(item.chartType)
                : getItemTypeIcon(item.type);

              const spanClass = item.span || "col-span-1";
              const cols = spanClass.includes("col-span-4") ? 4 :
                         spanClass.includes("col-span-3") ? 3 :
                         spanClass.includes("col-span-2") ? 2 : 1;

              return (
                <div
                  key={index}
                  className={`flex h-6 items-center justify-center rounded bg-background/60 col-span-${Math.min(cols, 4)}`}
                >
                  <Icon className="h-3 w-3 text-muted-foreground" />
                </div>
              );
            })}
          </div>
        </div>

        {/* Template Info */}
        <div className="space-y-2">
          <div className="flex flex-wrap gap-1">
            {itemTypes.map(type => (
              <Badge key={type} variant="secondary" className="text-xs">
                {type}
              </Badge>
            ))}
            {chartTypes.map(chartType => (
              <Badge key={chartType} variant="outline" className="text-xs">
                {chartType}
              </Badge>
            ))}
          </div>

          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{items.length} components</span>
            <span>{new Date(template.created_at).toLocaleDateString()}</span>
          </div>
        </div>

        <Button
          className="mt-4 w-full"
          onClick={() => onUseTemplate(template)}
        >
          <Plus className="mr-2 h-4 w-4" />
          Use Template
        </Button>
      </CardContent>
    </Card>
  );
}