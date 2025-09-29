import { AssistantMessageProps } from "@copilotkit/react-ui";
import { Markdown } from "@copilotkit/react-ui";
import { Loader } from "lucide-react";
import { isValidElement, type ReactNode, useEffect, useMemo, useRef } from "react";

const containsCodeBlock = (children: unknown): boolean => {
  if (!children) return false;
  const nodes = Array.isArray(children) ? children : [children];
  return nodes.some((child) => {
    if (!isValidElement(child)) {
      return false;
    }

    const childType = child.type as { displayName?: string; name?: string };
    const displayName = childType?.displayName || childType?.name;
    if (displayName === "CodeBlock") {
      return true;
    }

    return containsCodeBlock(child.props?.children);
  });
};

const HIGHLIGHT_LINE_REGEX = /^Highlight chart card:\s*(.+)$/gim;

const markdownOverrides = {
  p: ({ children, ...props }: { children: ReactNode }) => {
    if (containsCodeBlock(children)) {
      return (
        <div className="copilotKitMarkdownElement" {...props}>
          {children}
        </div>
      );
    }

    return (
      <p className="copilotKitMarkdownElement" {...props}>
        {children}
      </p>
    );
  },
};

export const CustomAssistantMessage = (props: AssistantMessageProps) => {
  const { message, isLoading, subComponent } = props;
  const highlightTimeoutsRef = useRef<Map<HTMLElement, number>>(new Map());
  const processedMessageRef = useRef<string | null>(null);

  const sanitizedMessage = useMemo(() => {
    if (!message) return "";
    const withoutDirectives = message.replace(/^Highlight chart card:.*$/gim, "");
    return withoutDirectives
      .split("\n")
      .filter((line, index, arr) => {
        // remove leading/trailing blank lines introduced by directive removal
        if (!line.trim()) {
          const prev = arr.slice(0, index).some((item) => item.trim().length > 0);
          const next = arr.slice(index + 1).some((item) => item.trim().length > 0);
          return prev && next;
        }
        return true;
      })
      .join("\n")
      .replace(/\n{3,}/g, "\n\n")
      .trimEnd();
  }, [message]);

  useEffect(() => {
    if (!message || processedMessageRef.current === message) {
      return;
    }

    const matches = [...message.matchAll(HIGHLIGHT_LINE_REGEX)];
    if (matches.length === 0) {
      return;
    }

    processedMessageRef.current = message;

    const chartIds = Array.from(
      new Set(
        matches
          .map((match) => match[1]?.trim())
          .map((id) => id?.replace(/^`+|`+$/g, ""))
          .map((id) => id?.replace(/[.,;:]+$/, ""))
          .filter((id): id is string => Boolean(id)),
      ),
    );

    if (chartIds.length === 0) {
      return;
    }

    const escapeId = (value: string) => {
      if (typeof window.CSS?.escape === "function") {
        return window.CSS.escape(value);
      }
      return value.replace(/[^a-zA-Z0-9_-]/g, (char) => `\\${char}`);
    };

    const highlightClass = "chart-card-highlight";

    const clearHighlight = (element: HTMLElement) => {
      element.classList.remove(highlightClass);
      element.removeAttribute("data-highlighted");
      const timeoutId = highlightTimeoutsRef.current.get(element);
      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId);
        highlightTimeoutsRef.current.delete(element);
      }
    };

    // Remove highlight from cards not in the new set
    const allCards = Array.from(
      document.querySelectorAll<HTMLElement>("[data-chart-id]"),
    );
    allCards.forEach((card) => {
      if (!chartIds.includes(card.dataset.chartId || "")) {
        clearHighlight(card);
      }
    });

    chartIds.forEach((chartId, index) => {
      const selector = `[data-chart-id="${escapeId(chartId)}"]`;
      const element = document.querySelector<HTMLElement>(selector);
      if (!element) {
        return;
      }

      clearHighlight(element);

      element.classList.add(highlightClass);
      element.setAttribute("data-highlighted", "true");

      if (index === 0) {
        element.scrollIntoView({ behavior: "smooth", block: "center" });
      }

      const timeoutId = window.setTimeout(() => {
        clearHighlight(element);
      }, 6000);

      highlightTimeoutsRef.current.set(element, timeoutId);
    });
  }, [message]);

  useEffect(() => {
    const activeTimeouts = highlightTimeoutsRef.current;

    return () => {
      activeTimeouts.forEach((timeoutId) => {
        window.clearTimeout(timeoutId);
      });
      activeTimeouts.clear();
    };
  }, []);

  return (
    <div className="pb-4">
      {(message || isLoading) && 
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-4">
            <div className="text-sm text-gray-700 dark:text-gray-300">
            <Markdown content={sanitizedMessage || message || ""} components={markdownOverrides} />
            {isLoading && (
                <div className="flex items-center gap-2 text-xs text-blue-500">
                <Loader className="h-3 w-3 animate-spin" />
                <span>Thinking...</span>
                </div>
            )}
            </div>
        </div>
      }
      
      {subComponent && <div>{subComponent}</div> }
    </div>
  );
};
