"use client"

import { useEffect, useMemo, useState } from "react";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { useSharedContext } from "@/lib/shared-context";
import { instructions } from "@/lib/prompts";
import { usePathname } from "next/navigation";

const deriveRoleFromPathname = (pathname: string | null): string => {
  if (!pathname) return "general";

  if (pathname === "/" || pathname.startsWith("/developer")) return "developer";
  if (pathname.startsWith("/tester")) return "tester";
  if (pathname.startsWith("/lab-admin")) return "lab-admin";
  if (pathname.startsWith("/executive")) return "executive";

  return "general";
};

export function ChatInterface() {
  const { prData, suggestionInstructions } = useSharedContext();
  const [isMounted, setIsMounted] = useState(false);
  const pathname = usePathname();
  const userRole = useMemo(() => deriveRoleFromPathname(pathname), [pathname]);

  const chatInstructions = useMemo(
    () => instructions.replace("{prData}", JSON.stringify(prData)),
    [prData]
  );

  useEffect(() => {
    if (process.env.NODE_ENV !== "production") {
      console.log("[ChatInterface] Instructions updated", {
        userRole,
        chatInstructions,
        suggestionInstructions,
      });
    }
  }, [chatInstructions, suggestionInstructions, userRole]);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    return (
      <div className="flex h-full w-80 flex-col border-l bg-background">
        <div className="flex items-center justify-between border-b px-4 py-4">
          <h2 className="font-semibold">EnterpriseX Assistant</h2>
        </div>
      </div>
    );
  }
  return (
    <div className="flex h-full w-80 flex-col border-l bg-background">
      <div className="flex items-center justify-between border-b px-4 py-4">
        <h2 className="font-semibold">EnterpriseX Assistant</h2>
      </div>
      <CopilotChat
        key={userRole}
        className="flex-1 min-h-0 py-4"
        instructions={chatInstructions}
      />
      <div className="border-t px-4 py-3 text-xs text-muted-foreground">
        <p className="font-medium text-foreground">Suggestion instructions</p>
        <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words">
          {suggestionInstructions || "(no suggestion instructions yet)"}
        </pre>
      </div>
    </div>
  );
}
