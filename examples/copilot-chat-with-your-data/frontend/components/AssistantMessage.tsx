"use client";

import { Loader } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useMemo } from "react";
import type { Components } from "react-markdown";
import { normalizeMarkdownTables } from "../lib/markdown";
import { useAgUiAgent } from "./ag-ui/AgUiProvider";

export type AssistantMessageProps = {
  content: string;
  isStreaming?: boolean;
};

export const AssistantMessage = ({ content, isStreaming }: AssistantMessageProps) => {
  const normalizedContent = normalizeMarkdownTables(content);
  const { highlightCharts } = useAgUiAgent();

  const { cleanedContent, suggestions } = useMemo(() => {
    const lines = normalizedContent.split(/\r?\n/);
    const suggestionItems: Array<{ label: string; id: string }> = [];
    const keptLines: string[] = [];

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed) {
        return;
      }

      if (
        trimmed.toLowerCase() === "highlight chart cards:" ||
        trimmed.toLowerCase() === "suggested charts:"
      ) {
        return;
      }

      if (trimmed.toLowerCase() === "suggested charts:") {
        return;
      }

      const match = trimmed.match(/^[-*]\s*\[([^\]]+)\]\(highlight:\/\/([^\)]+)\)/i);
      if (match) {
        const [, label, id] = match;
        if (label && id) {
          suggestionItems.push({ label, id });
        }
        return;
      }

      keptLines.push(line);
    });

    const compact = keptLines.join("\n").replace(/\n{2,}/g, "\n").trim();
    return {
      cleanedContent: compact,
      suggestions: suggestionItems,
    };
  }, [normalizedContent]);

  const markdownComponents = useMemo<Components>(() => ({
    a({ href, children, ...props }) {
      if (href?.startsWith("highlight://")) {
        const chartId = href.replace("highlight://", "");
        return (
          <button
            type="button"
            className="inline-flex cursor-pointer items-center gap-1 text-primary underline-offset-4 hover:underline"
            onClick={(event) => {
              event.preventDefault();
              if (chartId) {
                highlightCharts([chartId], { persistent: true });
              }
            }}
          >
            {children}
          </button>
        );
      }
      return (
        <a
          href={href ?? "#"}
          {...props}
          className="cursor-pointer text-primary underline-offset-4 hover:underline"
          target={href?.startsWith("http") ? "_blank" : undefined}
          rel={href?.startsWith("http") ? "noreferrer" : undefined}
        >
          {children}
        </a>
      );
    },
  }), [highlightCharts]);

  return (
    <div className="pb-4">
      <div className="rounded-lg border border-border bg-muted/60 p-3 shadow-sm">
        <div className="prose prose-sm space-y-2 text-muted-foreground dark:prose-invert">
          {cleanedContent ? (
            <ReactMarkdown components={markdownComponents} remarkPlugins={[remarkGfm]}>
              {cleanedContent}
            </ReactMarkdown>
          ) : null}
          {suggestions.length > 0 ? (
            <div className="mt-3 space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-primary/70">
                Suggested Charts
              </p>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((suggestion) => (
                  <button
                    key={`${suggestion.id}-${suggestion.label}`}
                    type="button"
                    onClick={() => highlightCharts([suggestion.id], { persistent: true })}
                    className="inline-flex cursor-pointer items-center justify-center rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-medium text-primary transition hover:bg-primary/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                  >
                    {suggestion.label}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
          {isStreaming && (
            <div className="mt-2 flex items-center gap-2 text-xs text-primary">
              <Loader className="h-3 w-3 animate-spin" />
              <span>Thinking...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
