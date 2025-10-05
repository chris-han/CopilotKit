"use client";

import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar, Edit, Eye, Trash2 } from "lucide-react";
import { Dashboard, getDashboardItemCount, getDashboardItemLabel } from "@/types/dashboard";

interface DashboardCardProps {
  dashboard: Dashboard;
  onDelete?: (dashboard: Dashboard) => void;
  showActions?: boolean;
  onClick?: (dashboard: Dashboard) => void;
}

export function DashboardCard({
  dashboard,
  onDelete,
  showActions = true,
  onClick
}: DashboardCardProps) {
  // Calculate item count using unified helper
  const itemCount = getDashboardItemCount(dashboard);
  const itemLabel = getDashboardItemLabel(dashboard);

  const handleCardClick = () => {
    if (onClick) {
      onClick(dashboard);
    }
  };

  return (
    <Card
      className={`group relative transition-all hover:shadow-lg ${onClick ? 'cursor-pointer' : ''}`}
      onClick={handleCardClick}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className={`text-base ${onClick ? '' : 'truncate'}`}>
              {dashboard.name}
            </CardTitle>
            {dashboard.description && (
              <CardDescription className={`text-sm ${onClick ? '' : 'line-clamp-2'}`}>
                {dashboard.description}
              </CardDescription>
            )}
          </div>
          {dashboard.is_public && (
            <Badge variant="secondary" className="ml-2">
              Public
            </Badge>
          )}
          {!showActions && (
            <span className="text-sm font-normal text-muted-foreground">
              {itemCount} {itemLabel}
            </span>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {/* Dashboard Preview */}
        {showActions && (
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
        )}

        {/* Dashboard Items List (when not showing actions) */}
        {!showActions && itemCount > 0 && dashboard.layout_config?.items && (
          <div className="mb-4">
            <div className="space-y-2">
              <p className="text-sm font-medium">Dashboard Items:</p>
              <div className="space-y-1">
                {dashboard.layout_config.items?.slice(0, 3).map((item) => (
                  <div key={item.id} className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <span className="w-2 h-2 bg-primary rounded-full"></span>
                    <span className="truncate">{item.title}</span>
                  </div>
                ))}
                {itemCount > 3 && (
                  <p className="text-xs text-muted-foreground">
                    +{itemCount - 3} more items
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
        {!showActions && itemCount === 0 && (
          <p className="text-sm text-muted-foreground mb-4">No items added yet</p>
        )}

        {/* Dashboard Info */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            {showActions && <span>{itemCount} {itemLabel}</span>}
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span className="text-xs">
                Created: {new Date(dashboard.created_at).toLocaleDateString()}
                {dashboard.updated_at !== dashboard.created_at && (
                  <span> • Updated: {new Date(dashboard.updated_at).toLocaleDateString()}</span>
                )}
              </span>
            </span>
          </div>

          {/* Actions */}
          {showActions && (
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
              {onDelete && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(dashboard);
                  }}
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}