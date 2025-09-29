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
      <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="text-sm text-gray-700 dark:text-gray-300 space-y-2">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizedContent}</ReactMarkdown>
          {isStreaming && (
            <div className="flex items-center gap-2 text-xs text-blue-500 mt-2">
              <Loader className="h-3 w-3 animate-spin" />
              <span>Thinking...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
