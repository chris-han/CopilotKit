"use client"

import { useEffect, useMemo, useState } from "react";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { useSharedContext } from "@/lib/shared-context";
import { instructions } from "@/lib/prompts";
import { usePathname } from "next/navigation";
export function ChatInterface() {
  const { prData } = useSharedContext();
  const [isMounted, setIsMounted] = useState(false);
  const pathname = usePathname();

  const chatInstructions = useMemo(
    () => instructions.replace("{prData}", JSON.stringify(prData)),
    [prData]
  );

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
        key={pathname}
        className="flex-1 min-h-0 py-4"
        instructions={chatInstructions}
      />
    </div>
  );
}
