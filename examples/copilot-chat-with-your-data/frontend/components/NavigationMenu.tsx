"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import { ChevronLeft, ChevronRight, Home, LineChart, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Sheet, SheetContent, SheetHeader, SheetTitle } from "./ui/sheet";

const NAV_EXPANDED_CLASS = "w-72"; // 18rem
const NAV_COLLAPSED_CLASS = "w-20"; // 5rem
const NAV_EXPANDED_WIDTH = "18rem";
const NAV_COLLAPSED_WIDTH = "5rem";
const NAV_EXPANDED_HORIZONTAL_PADDING_REM = 1; // px-4
const NAV_COLLAPSED_HORIZONTAL_PADDING_REM = 0.5; // px-2
const TOGGLE_RADIUS_REM = 1.125; // half of w-9 (2.25rem)
const TOGGLE_CLIP_PATH_EXPANDED = "inset(0 50% 0 0 round 999px 0 0 999px)";
const TOGGLE_CLIP_PATH_COLLAPSED = "inset(0 0 0 50% round 0 999px 999px 0)";

type NavigationItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};

const NAVIGATION_ITEMS: NavigationItem[] = [
  { label: "Overview", href: "/", icon: Home },
  { label: "Dynamic Dashboard", href: "/dynamic-dashboard", icon: LineChart },
  { label: "LIDA Analytics", href: "/lida", icon: Sparkles },
];

export function NavigationMenu() {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const normalizedPath = useMemo(() => {
    if (!pathname) {
      return "/";
    }
    return pathname.endsWith("/") && pathname.length > 1
      ? pathname.slice(0, -1)
      : pathname;
  }, [pathname]);

  useEffect(() => {
    if (typeof document === "undefined") {
      return;
    }
    document.documentElement.style.setProperty(
      "--navigation-width",
      isCollapsed ? NAV_COLLAPSED_WIDTH : NAV_EXPANDED_WIDTH,
    );
  }, [isCollapsed]);

  const toggleRightOffsetRem = -(
    TOGGLE_RADIUS_REM +
      (isCollapsed ? NAV_COLLAPSED_HORIZONTAL_PADDING_REM : NAV_EXPANDED_HORIZONTAL_PADDING_REM)
  );
  const toggleClipPath = isCollapsed ? TOGGLE_CLIP_PATH_COLLAPSED : TOGGLE_CLIP_PATH_EXPANDED;

  return (
    <Sheet open modal={false} onOpenChange={() => {}}>
      <SheetContent
        side="left"
        hideOverlay
        className={clsx(
          isCollapsed ? NAV_COLLAPSED_CLASS : NAV_EXPANDED_CLASS,
          "inset-y-0 left-0 h-full border-r border-border/50 bg-background py-6",
          isCollapsed ? "px-2" : "px-4",
          "hidden md:flex"
        )}
      >
        <SheetHeader className="sr-only">
          <SheetTitle>Navigation Menu</SheetTitle>
        </SheetHeader>
        <div className="flex h-full w-full flex-col">
          <div
            className={clsx(
              "relative flex w-full items-center",
              !isCollapsed ? "justify-start gap-3" : "justify-center",
            )}
          >
            <Link
              href="/"
              className={clsx(
                "flex flex-1 items-center gap-2",
                isCollapsed ? "justify-center" : "justify-start",
                !isCollapsed && "pr-14",
              )}
              aria-label="ABI Home"
            >
              <svg
                width="40"
                height="40"
                viewBox="0 0 40 40"
                role="img"
                aria-hidden="true"
                className="text-primary"
              >
                <rect x="0" y="0" width="40" height="40" rx="10" fill="currentColor" />
                <text
                  x="20"
                  y="25"
                  textAnchor="middle"
                  fontFamily="Inter, sans-serif"
                  fontSize="18"
                  fontWeight="700"
                  fill="var(--primary-foreground)"
                >
                  ABI
                </text>
              </svg>
              {!isCollapsed && (
                <span className="text-lg font-semibold text-foreground">
                  ABI Analytics
                </span>
              )}
            </Link>
            <button
              type="button"
              onClick={() => setIsCollapsed((previous) => !previous)}
              className="absolute top-1/2 inline-flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full border border-border/60 bg-card text-muted-foreground shadow-lg transition hover:bg-muted"
              aria-pressed={isCollapsed}
              aria-label={isCollapsed ? "Expand navigation" : "Collapse navigation"}
              style={{ right: `${toggleRightOffsetRem}rem`, clipPath: toggleClipPath }}
            >
              {isCollapsed ? (
                <ChevronRight className="h-4 w-4 translate-x-1" aria-hidden="true" />
              ) : (
                <ChevronLeft className="h-4 w-4 -translate-x-1" aria-hidden="true" />
              )}
            </button>
          </div>

          <nav
            className={clsx("mt-8 flex-1", isCollapsed && "mt-6 w-full")}
            aria-label="Primary navigation"
          >
            <ul
              className={clsx(
                "flex flex-col gap-1",
                isCollapsed && "items-center gap-2",
              )}
            >
              {NAVIGATION_ITEMS.map((item) => {
                const href = item.href === "/" ? "/" : item.href.replace(/\/$/, "");
                const isActive = normalizedPath === href;
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={clsx(
                        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                        "text-muted-foreground hover:text-foreground hover:bg-muted",
                        isActive && "bg-muted text-foreground",
                        isCollapsed && "justify-center gap-0 px-2"
                      )}
                      aria-label={item.label}
                    >
                      <Icon className="h-4 w-4" aria-hidden="true" />
                      {!isCollapsed && <span>{item.label}</span>}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          {!isCollapsed && (
            <div className="mt-auto text-xs text-muted-foreground">
              <p>© {new Date().getFullYear()} ABI Analytics Intelligence.</p>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
