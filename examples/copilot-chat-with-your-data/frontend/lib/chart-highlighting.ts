const HIGHLIGHT_CLASS = "chart-card-highlight";
const highlights = new Map<HTMLElement, number>();
const activeChartFocus = new Map<string, ChartFocusSpec | null>();

type ChartFocusSpec = {
  seriesIndex?: number;
  seriesId?: string;
  seriesName?: string;
  dataIndex?: number;
  dataName?: string;
};

export type ChartFocusTarget = {
  chartId: string;
} & ChartFocusSpec;

export type ChartFocusEventDetail = {
  chartId: string;
  target: ChartFocusSpec | null;
};

export const CHART_FOCUS_EVENT = "chart.dimension-focus";

export const STRATEGIC_COMMENTARY_TAB_EVENT = "strategic-commentary.tab";

export type StrategicCommentaryTabEventDetail = {
  tab: string;
};

export function dispatchStrategicCommentaryTab(tab: string) {
  if (typeof window === "undefined" || !tab) {
    return;
  }
  const event = new CustomEvent<StrategicCommentaryTabEventDetail>(STRATEGIC_COMMENTARY_TAB_EVENT, {
    detail: { tab },
  });
  window.dispatchEvent(event);
}

export type HighlightOptions = {
  durationMs?: number;
  persistent?: boolean;
  focusTargets?: ChartFocusTarget[];
};

function normaliseFocusTarget(target?: ChartFocusTarget): ChartFocusSpec | null {
  if (!target || !target.chartId) {
    return null;
  }
  const spec: ChartFocusSpec = {
    seriesIndex: target.seriesIndex,
    seriesId: target.seriesId,
    seriesName: target.seriesName,
    dataIndex: target.dataIndex,
    dataName: target.dataName,
  };
  const hasValues = Object.values(spec).some((value) => value !== undefined);
  return hasValues ? spec : null;
}

function isSameFocus(a: ChartFocusSpec | null | undefined, b: ChartFocusSpec | null | undefined) {
  if (!a && !b) {
    return true;
  }
  if (!a || !b) {
    return false;
  }
  return (
    a.seriesIndex === b.seriesIndex &&
    a.seriesId === b.seriesId &&
    a.seriesName === b.seriesName &&
    a.dataIndex === b.dataIndex &&
    a.dataName === b.dataName
  );
}

function dispatchChartFocus(chartId: string, target: ChartFocusSpec | null) {
  if (typeof window === "undefined") {
    return;
  }
  const detail: ChartFocusEventDetail = { chartId, target };
  window.dispatchEvent(new CustomEvent(CHART_FOCUS_EVENT, { detail }));
}

function escapeChartId(id: string): string {
  if (typeof window !== "undefined" && typeof window.CSS?.escape === "function") {
    return window.CSS.escape(id);
  }
  return id.replace(/[^a-zA-Z0-9_-]/g, (char) => `\\${char}`);
}

function clearHighlight(element: HTMLElement) {
  element.classList.remove(HIGHLIGHT_CLASS);
  element.removeAttribute("data-highlighted");
  const timeoutId = highlights.get(element);
  if (timeoutId !== undefined) {
    window.clearTimeout(timeoutId);
    highlights.delete(element);
  }
}

export function clearAllHighlights() {
  const cards = Array.from(document.querySelectorAll<HTMLElement>("[data-chart-id]"));
  cards.forEach((card) => clearHighlight(card));
  if (typeof window !== "undefined") {
    activeChartFocus.forEach((_value, chartId) => {
      dispatchChartFocus(chartId, null);
    });
  }
  activeChartFocus.clear();
}

export function applyHighlights(chartIds: string[], options?: HighlightOptions) {
  if (typeof window === "undefined") {
    return;
  }

  const uniqueIds = Array.from(new Set(chartIds.filter(Boolean)));
  if (uniqueIds.length === 0) {
    clearAllHighlights();
    return;
  }

  const allCards = Array.from(document.querySelectorAll<HTMLElement>("[data-chart-id]"));
  allCards.forEach((card) => {
    if (!uniqueIds.includes(card.dataset.chartId || "")) {
      clearHighlight(card);
    }
  });

  const { persistent = false, focusTargets } = options ?? {};
  const durationMs = options?.durationMs ?? 6000;

  const highlightedSet = new Set(uniqueIds);
  const focusMap = new Map<string, ChartFocusSpec | null>();
  if (Array.isArray(focusTargets)) {
    focusTargets.forEach((target) => {
      if (!target?.chartId) {
        return;
      }
      focusMap.set(target.chartId, normaliseFocusTarget(target));
    });
  }

  uniqueIds.forEach((rawId, index) => {
    const selector = `[data-chart-id="${escapeChartId(rawId)}"]`;
    const element = document.querySelector<HTMLElement>(selector);
    if (!element) {
      return;
    }

    clearHighlight(element);
    element.classList.add(HIGHLIGHT_CLASS);
    element.setAttribute("data-highlighted", "true");

    if (index === 0) {
      element.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    if (!persistent && Number.isFinite(durationMs) && durationMs > 0) {
      const timeoutId = window.setTimeout(() => {
        clearHighlight(element);
      }, durationMs);
      highlights.set(element, timeoutId);
    }
  });

  const chartsToProcess = new Set<string>([
    ...Array.from(highlightedSet),
    ...Array.from(activeChartFocus.keys()),
    ...Array.from(focusMap.keys()),
  ]);

  chartsToProcess.forEach((chartId) => {
    if (!chartId) {
      return;
    }
    const shouldHighlight = highlightedSet.has(chartId);
    const nextFocus = shouldHighlight ? focusMap.get(chartId) ?? null : null;
    const previousFocus = activeChartFocus.get(chartId) ?? null;
    if (!isSameFocus(previousFocus, nextFocus)) {
      dispatchChartFocus(chartId, nextFocus);
    }
    if (shouldHighlight || nextFocus) {
      activeChartFocus.set(chartId, nextFocus);
    } else if (activeChartFocus.has(chartId)) {
      activeChartFocus.delete(chartId);
    }
  });
}
