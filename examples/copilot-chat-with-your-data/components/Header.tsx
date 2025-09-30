"use client";

import {
  forwardRef,
  useImperativeHandle,
  useLayoutEffect,
  useRef,
} from "react";
import type { ComponentPropsWithoutRef } from "react";
import { ThemeToggle } from "./ThemeToggle";
import clsx from "clsx";
import { PanelRightClose, PanelRightOpen } from "lucide-react";

type HeaderProps = ComponentPropsWithoutRef<"header"> & {
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
};

export const Header = forwardRef<HTMLElement, HeaderProps>(function Header(
  { className, onToggleSidebar, isSidebarOpen, ...props },
  ref,
) {
  const internalRef = useRef<HTMLElement | null>(null);

  useImperativeHandle(ref, () => internalRef.current, []);

  useLayoutEffect(() => {
    const node = internalRef.current;
    if (!node || typeof window === "undefined") {
      return;
    }

    const setHeight = () => {
      const { height } = node.getBoundingClientRect();
      document.documentElement.style.setProperty(
        "--app-header-height",
        `${Math.round(height)}px`,
      );
    };

    setHeight();

    const observer = typeof ResizeObserver !== "undefined"
      ? new ResizeObserver(() => setHeight())
      : null;

    observer?.observe(node);
    window.addEventListener("resize", setHeight);

    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", setHeight);
    };
  }, []);

  return (
    <header
      ref={(value) => {
        internalRef.current = value;
        if (typeof ref === "function") {
          ref(value);
        } else if (ref) {
          ref.current = value;
        }
      }}
      className={clsx(
        "sticky top-0 z-50 border-b border-border bg-background",
        className,
      )}
      {...props}
    >
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <div>
          <h1 className="text-2xl font-medium text-foreground">Data Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Interactive data visualization with AI assistance
          </p>
        </div>
        <div className="flex items-center gap-2">
          {onToggleSidebar && (
            <button
              type="button"
              onClick={onToggleSidebar}
              className="inline-flex h-10 items-center justify-center rounded-md border border-border bg-card px-3 text-sm font-medium text-foreground shadow-sm transition hover:bg-muted"
              aria-pressed={Boolean(isSidebarOpen)}
              aria-label={isSidebarOpen ? "Hide data assistant" : "Show data assistant"}
            >
              {isSidebarOpen ? (
                <>
                  <PanelRightClose className="mr-2 h-4 w-4" />
                  <span className="hidden sm:inline">Hide Assistant</span>
                </>
              ) : (
                <>
                  <PanelRightOpen className="mr-2 h-4 w-4" />
                  <span className="hidden sm:inline">Show Assistant</span>
                </>
              )}
              <span className="sm:hidden">Assistant</span>
            </button>
          )}
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
});
