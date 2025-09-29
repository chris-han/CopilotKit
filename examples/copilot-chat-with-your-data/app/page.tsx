"use client";

import { useEffect, useMemo, useState } from "react";
import { Dashboard } from "../components/Dashboard";
import { Header } from "../components/Header";
import { Footer } from "../components/Footer";
import { AgUiSidebar } from "../components/ag-ui/AgUiSidebar";

const MIN_DASHBOARD_WIDTH_PX = 1024;
const SIDEBAR_WIDTH_PX = 28 * 16; // Copilot sidebar expands to 28rem

export default function Home() {
  const [windowWidth, setWindowWidth] = useState<number | null>(null);

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

  const layoutClasses = `min-h-screen bg-gray-50 flex flex-col transition-[padding] duration-300 ${
    shouldOffsetLayout ? "pr-[28rem]" : ""
  }`;

  const mainClasses = `w-full max-w-7xl lg:min-w-[64rem] mx-auto py-6 px-4 sm:px-6 lg:px-8 flex-grow transition-[padding] duration-300 ${
    shouldOffsetLayout ? "pr-8" : ""
  }`;

  return (
    <div className={layoutClasses}>
      <Header />
      <main
        className={mainClasses}
        style={shouldOffsetLayout ? { minWidth: MIN_DASHBOARD_WIDTH_PX } : undefined}
      >
        <Dashboard />
      </main>
      <Footer />
      <AgUiSidebar />
    </div>
  );
}
