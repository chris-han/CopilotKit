"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";

import { Header } from "./Header";
import { Footer } from "./Footer";
import { NavigationMenu } from "./NavigationMenu";
import { AgUiSidebar } from "./ag-ui/AgUiSidebar";

const MIN_DASHBOARD_WIDTH_PX = 1024;
const SIDEBAR_WIDTH_PX = 28 * 16; // Copilot sidebar expands to 28rem

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const [windowWidth, setWindowWidth] = useState<number | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const didManuallyToggleSidebar = useRef(false);

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const shouldOffsetLayout = useMemo(() => {
    if (windowWidth === null) {
      return false;
    }
    return windowWidth >= MIN_DASHBOARD_WIDTH_PX + SIDEBAR_WIDTH_PX;
  }, [windowWidth]);

  useEffect(() => {
    if (windowWidth === null || didManuallyToggleSidebar.current) {
      return;
    }
    setIsSidebarOpen(windowWidth >= MIN_DASHBOARD_WIDTH_PX + SIDEBAR_WIDTH_PX);
  }, [windowWidth]);

  const layoutClasses = clsx(
    "min-h-screen bg-background flex flex-col transition-[padding] duration-300",
    "md:pl-[var(--navigation-width,18rem)]",
  );

  const mainClasses = `w-full max-w-7xl lg:min-w-[64rem] mx-auto py-6 px-4 sm:px-6 lg:px-8 flex-grow transition-[padding] duration-300 ${
    shouldOffsetLayout ? "pr-8" : ""
  }`;

  const mainWrapperClasses = clsx(
    "flex flex-1 flex-col transition-[padding] duration-300",
    shouldOffsetLayout && isSidebarOpen && "lg:pr-[28rem]",
  );

  const handleToggleSidebar = () => {
    didManuallyToggleSidebar.current = true;
    setIsSidebarOpen((previous) => !previous);
  };

  const handleCloseSidebar = () => {
    didManuallyToggleSidebar.current = true;
    setIsSidebarOpen(false);
  };

  return (
    <>
      <NavigationMenu />
      <div className={layoutClasses}>
        <Header
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={handleToggleSidebar}
          sidebarOffset={Boolean(isSidebarOpen && shouldOffsetLayout)}
        />
      <div className={mainWrapperClasses}>
        <main
          className={mainClasses}
          style={shouldOffsetLayout ? { minWidth: MIN_DASHBOARD_WIDTH_PX } : undefined}
        >
          {children}
        </main>
        <Footer />
      </div>
      <AgUiSidebar
        open={isSidebarOpen}
        docked={Boolean(isSidebarOpen && shouldOffsetLayout)}
        onClose={handleCloseSidebar}
      />
      </div>
    </>
  );
}
