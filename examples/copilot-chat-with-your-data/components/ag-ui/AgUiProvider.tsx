"use client";

import { HttpAgent } from "@ag-ui/client";
import { EventType } from "@ag-ui/core";
import type { Message } from "@ag-ui/core";
import {
  PropsWithChildren,
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";
import type { Subscription } from "rxjs";
import { useEffect } from "react";

import { applyHighlights, clearAllHighlights } from "../../lib/chart-highlighting";
import { prompt as defaultPrompt } from "../../lib/prompt";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  pending?: boolean;
};

export type AgUiContextValue = {
  messages: ChatMessage[];
  isRunning: boolean;
  error: string | null;
  sendMessage: (content: string) => void;
};

const AgUiContext = createContext<AgUiContextValue | null>(null);

function generateId(prefix: string) {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Math.random().toString(36).slice(2)}`;
}

type ProviderProps = PropsWithChildren<{
  runtimeUrl: string;
  systemPrompt?: string;
}>;

export function AgUiProvider({ children, runtimeUrl, systemPrompt }: ProviderProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const agentRef = useRef<HttpAgent | null>(null);
  const subscriptionRef = useRef<Subscription | null>(null);
  const threadIdRef = useRef<string>(generateId("thread"));
  const historyRef = useRef<Message[]>([]);
  const systemMessage = useMemo(() => systemPrompt || defaultPrompt, [systemPrompt]);

  if (agentRef.current == null) {
    agentRef.current = new HttpAgent({
      url: runtimeUrl,
    });
  }

  useEffect(() => {
    return () => {
      subscriptionRef.current?.unsubscribe();
    };
  }, []);

  const ensureSystemMessage = useCallback(() => {
    if (!systemMessage) {
      return;
    }
    if (!historyRef.current.some((msg) => msg.role === "system")) {
      historyRef.current = [
        {
          id: "system-message",
          role: "system",
          content: systemMessage,
        },
        ...historyRef.current,
      ];
    }
  }, [systemMessage]);

  const sendMessage = useCallback(
    (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || !agentRef.current) {
        return;
      }
      if (isRunning) {
        return;
      }

      ensureSystemMessage();
      setError(null);

      const userMessageId = generateId("user");
      const userMessage: Message = {
        id: userMessageId,
        role: "user",
        content: trimmed,
      };

      historyRef.current = [...historyRef.current, userMessage];
      setMessages((prev) => [...prev, { id: userMessageId, role: "user", content: trimmed }]);

      const runId = generateId("run");
      const agent = agentRef.current;
      const observable = agent.runAgent({
        threadId: threadIdRef.current,
        runId,
        messages: historyRef.current,
        tools: [],
        context: [],
        state: {},
        forwardedProps: {},
      });

      setIsRunning(true);
      clearAllHighlights();

      subscriptionRef.current?.unsubscribe();

      const subscription = observable.subscribe({
        next: (event) => {
          switch (event.type) {
            case EventType.RUN_STARTED:
              setIsRunning(true);
              break;
            case EventType.TEXT_MESSAGE_START: {
              const assistantId = event.messageId ?? generateId("assistant");
              const assistantMessage: Message = {
                id: assistantId,
                role: "assistant",
                content: "",
              };
              historyRef.current = [...historyRef.current, assistantMessage];
              setMessages((prev) => [
                ...prev,
                { id: assistantId, role: "assistant", content: "", pending: true },
              ]);
              break;
            }
            case EventType.TEXT_MESSAGE_CONTENT: {
              const { messageId, delta } = event;
              if (!messageId || !delta) {
                break;
              }
              historyRef.current = historyRef.current.map((msg) =>
                msg.id === messageId ? { ...msg, content: `${msg.content}${delta}` } : msg,
              );
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === messageId
                    ? { ...msg, content: `${msg.content}${delta}` }
                    : msg,
                ),
              );
              break;
            }
            case EventType.TEXT_MESSAGE_END: {
              const { messageId } = event;
              if (!messageId) {
                break;
              }
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === messageId ? { ...msg, pending: false } : msg,
                ),
              );
              break;
            }
            case EventType.RUN_FINISHED:
              setIsRunning(false);
              break;
            case EventType.RUN_ERROR:
              setIsRunning(false);
              setError(event.message ?? "Agent error");
              break;
            case EventType.CUSTOM:
              if (event.name === "chart.highlight") {
                const value = event.value ?? {};
                const ids = Array.isArray(value.chartIds)
                  ? value.chartIds
                  : value.chartId
                    ? [value.chartId]
                    : [];
                if (ids.length > 0) {
                  applyHighlights(ids);
                }
              }
              break;
            default:
              break;
          }
        },
        error: (err) => {
          console.error("AG-UI stream error", err);
          setIsRunning(false);
          setError(err?.message ?? String(err));
        },
        complete: () => {
          setIsRunning(false);
        },
      });

      subscriptionRef.current = subscription;
    },
    [ensureSystemMessage, isRunning],
  );

  return (
    <AgUiContext.Provider value={{ messages, isRunning, error, sendMessage }}>
      {children}
    </AgUiContext.Provider>
  );
}

export function useAgUiAgent(): AgUiContextValue {
  const ctx = useContext(AgUiContext);
  if (!ctx) {
    throw new Error("useAgUiAgent must be used within an AgUiProvider");
  }
  return ctx;
}
