"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import { Dashboard } from "../components/Dashboard";
import { Header } from "../components/Header";
import { Footer } from "../components/Footer";
import { CustomAssistantMessage } from "../components/AssistantMessage";
import { prompt } from "../lib/prompt";
import { useCopilotReadable } from "@copilotkit/react-core";

const CopilotSidebar = dynamic(
  () => import("@copilotkit/react-ui").then((mod) => mod.CopilotSidebar),
  { ssr: false },
);

const MIN_DASHBOARD_WIDTH_PX = 1024;
const SIDEBAR_WIDTH_PX = 28 * 16; // Copilot sidebar expands to 28rem

export default function Home() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [windowWidth, setWindowWidth] = useState(() =>
    typeof window === "undefined" ? 0 : window.innerWidth,
  );

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const shouldOffsetLayout = useMemo(() => {
    if (!isSidebarOpen) return false;
    return windowWidth >= MIN_DASHBOARD_WIDTH_PX + SIDEBAR_WIDTH_PX;
  }, [isSidebarOpen, windowWidth]);

  useCopilotReadable({
    description: "Current time",
    value: new Date().toLocaleTimeString(),
  });

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
      <div>
        <CopilotSidebar
          instructions={prompt}
          AssistantMessage={CustomAssistantMessage}
          labels={{
            title: "Data Assistant",
            initial: "Hello, I'm here to help you understand your data. How can I help?",
            placeholder: "Ask about sales, trends, or metrics...",
          }}
          onSetOpen={setIsSidebarOpen}
        />
      </div>
    </div>
  );
}

