import { Loader } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { normalizeMarkdownTables } from "../lib/markdown";

export type AssistantMessageProps = {
  content: string;
  isStreaming?: boolean;
};

export const AssistantMessage = ({ content, isStreaming }: AssistantMessageProps) => {
  const normalizedContent = normalizeMarkdownTables(content);

  return (
    <div className="pb-4">
      <div className="rounded-lg border border-border bg-muted/60 p-3 shadow-sm">
        <div className="prose prose-sm space-y-2 text-muted-foreground dark:prose-invert">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizedContent}</ReactMarkdown>
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
