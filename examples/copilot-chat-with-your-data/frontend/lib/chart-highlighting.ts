const HIGHLIGHT_CLASS = "chart-card-highlight";
const highlights = new Map<HTMLElement, number>();

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
};

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

  const { persistent = false } = options ?? {};
  const durationMs = options?.durationMs ?? 6000;

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
}
