"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { DataStoryStep, DataStoryStatus } from "../../hooks/useDataStory";

interface DataStoryTimelineProps {
  steps: DataStoryStep[];
  activeStepId?: string;
  status: DataStoryStatus;
  onReview: (stepId: string) => void;
}

export function DataStoryTimeline({ steps, activeStepId, status, onReview }: DataStoryTimelineProps) {
  if (!steps.length) {
    return null;
  }

  return (
    <div className="mt-4">
      <div className="mb-3 flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-900">Data Story Timeline</h4>
        <span className="text-xs text-gray-500 capitalize">{status}</span>
      </div>
      <ol className="space-y-4 border-l border-gray-200 pl-4">
        {steps.map((step, index) => {
          const isActive = step.id === activeStepId;
          return (
            <li key={step.id} className="relative">
              <span
                className={`absolute -left-2 top-1.5 flex h-3 w-3 -translate-x-1/2 rounded-full ${
                  isActive ? "bg-blue-600" : "bg-gray-300"
                }`}
              />
              <div className="rounded-md border border-gray-200 bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Step {index + 1}</p>
                    <h5 className="text-sm font-semibold text-gray-900">{step.title}</h5>
                  </div>
                  <button
                    type="button"
                    onClick={() => onReview(step.id)}
                    className="text-xs text-blue-600 hover:text-blue-700"
                  >
                    Review
                  </button>
                </div>
                <div className="prose prose-sm mt-2 text-gray-700">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{step.markdown}</ReactMarkdown>
                </div>
                {step.kpis?.length ? (
                  <div className="mt-3 grid gap-2 sm:grid-cols-2">
                    {step.kpis.map((kpi) => (
                      <div
                        key={`${step.id}-${kpi.label}`}
                        className="rounded border border-gray-100 bg-gray-50 px-3 py-2"
                      >
                        <p className="text-xs text-gray-500">{kpi.label}</p>
                        <p className="text-sm font-semibold text-gray-800">{kpi.value}</p>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
