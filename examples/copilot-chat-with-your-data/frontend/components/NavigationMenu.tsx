"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMemo } from "react";
import clsx from "clsx";

import { Sheet, SheetContent, SheetHeader, SheetTitle } from "./ui/sheet";

const NAV_WIDTH_CLASS = "w-72"; // 18rem

type NavigationItem = {
  label: string;
  href: string;
};

const NAVIGATION_ITEMS: NavigationItem[] = [
  { label: "Overview", href: "/" },
  { label: "Dynamic Dashboard", href: "/dynamic-dashboard" },
];

export function NavigationMenu() {
  const pathname = usePathname();

  const normalizedPath = useMemo(() => {
    if (!pathname) {
      return "/";
    }
    return pathname.endsWith("/") && pathname.length > 1
      ? pathname.slice(0, -1)
      : pathname;
  }, [pathname]);

  return (
    <Sheet open modal={false} onOpenChange={() => {}}>
      <SheetContent
        side="left"
        hideOverlay
        className={clsx(
          NAV_WIDTH_CLASS,
          "inset-y-0 left-0 h-full border-r border-border/50 bg-background px-4 py-6",
          "hidden gap-6 md:flex"
        )}
      >
        <SheetHeader className="sr-only">
          <SheetTitle>Navigation Menu</SheetTitle>
        </SheetHeader>
        <div className="flex h-full w-full flex-col">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2" aria-label="ABI Home">
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
              <span className="text-lg font-semibold text-foreground">ABI Analytics</span>
            </Link>
          </div>

          <nav className="mt-8 flex-1">
            <ul className="flex flex-col gap-1">
              {NAVIGATION_ITEMS.map((item) => {
                const href = item.href === "/" ? "/" : item.href.replace(/\/$/, "");
                const isActive = normalizedPath === href;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={clsx(
                        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                        "text-muted-foreground hover:text-foreground hover:bg-muted",
                        isActive && "bg-muted text-foreground"
                      )}
                    >
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="text-xs text-muted-foreground">
            <p>© {new Date().getFullYear()} ABI Analytics Intelligence.</p>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
