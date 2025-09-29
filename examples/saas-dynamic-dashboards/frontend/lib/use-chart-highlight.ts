"use client"

import { useCallback, useEffect } from "react"
import { useSharedContext } from "@/lib/shared-context"

const HIGHLIGHT_FLAG_KEYS = [
  "highlight",
  "highlighted",
  "isHighlighted",
  "shouldHighlight",
  "focus",
  "focused",
  "spotlight",
]

const HIGHLIGHT_ID_KEYS = [
  "chartId",
  "id",
  "cardId",
  "target",
  "targetChart",
  "highlightId",
  "highlightChartId",
  "highlightedChartId",
  "focusChartId",
  "spotlightChartId",
]

const POSITIVE_STRINGS = new Set(["true", "1", "yes", "y", "on", "focus", "highlight", "spotlight"])
const NEGATIVE_STRINGS = new Set(["false", "0", "no", "n", "off"])

const toRecord = (value: unknown): Record<string, unknown> | undefined => {
  if (typeof value === "object" && value !== null) {
    return value as Record<string, unknown>
  }
  return undefined
}

const getFirstDefined = (source: Record<string, unknown> | undefined, keys: string[]) => {
  if (!source) return undefined
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(source, key)) {
      return source[key]
    }
  }
  return undefined
}

const resolveCandidate = (chartId: string, candidate: unknown): boolean | undefined => {
  if (candidate === undefined || candidate === null) {
    return undefined
  }

  if (typeof candidate === "boolean") {
    return candidate
  }

  if (typeof candidate === "string") {
    const normalized = candidate.trim().toLowerCase()
    if (!normalized) {
      return undefined
    }
    if (normalized === chartId.toLowerCase()) {
      return true
    }
    if (POSITIVE_STRINGS.has(normalized)) {
      return true
    }
    if (NEGATIVE_STRINGS.has(normalized)) {
      return false
    }
    return undefined
  }

  if (typeof candidate === "number") {
    return candidate > 0
  }

  if (Array.isArray(candidate)) {
    for (const entry of candidate) {
      const resolved = resolveCandidate(chartId, entry)
      if (resolved !== undefined) {
        return resolved
      }
    }
    return undefined
  }

  const nestedRecord = toRecord(candidate)
  if (!nestedRecord) {
    return undefined
  }

  const nestedId = getFirstDefined(nestedRecord, HIGHLIGHT_ID_KEYS)
  if (nestedId !== undefined) {
    const resolved = resolveCandidate(chartId, nestedId)
    if (resolved !== undefined) {
      return resolved
    }
  }

  const nestedFlag = getFirstDefined(nestedRecord, HIGHLIGHT_FLAG_KEYS)
  if (nestedFlag !== undefined) {
    return resolveCandidate(chartId, nestedFlag)
  }

  return undefined
}

export function resolveChartHighlightIntent(chartId: string, rawArgs: unknown): boolean {
  const args = toRecord(rawArgs)
  if (!args) {
    return false
  }

  const directId = resolveCandidate(chartId, getFirstDefined(args, HIGHLIGHT_ID_KEYS))
  if (directId !== undefined) {
    return directId
  }

  const directFlag = resolveCandidate(chartId, getFirstDefined(args, HIGHLIGHT_FLAG_KEYS))
  if (directFlag !== undefined) {
    return directFlag
  }

  const meta = toRecord(getFirstDefined(args, ["meta", "metadata"]))
  if (meta) {
    const metaId = resolveCandidate(chartId, getFirstDefined(meta, HIGHLIGHT_ID_KEYS))
    if (metaId !== undefined) {
      return metaId
    }
    const metaFlag = resolveCandidate(chartId, getFirstDefined(meta, HIGHLIGHT_FLAG_KEYS))
    if (metaFlag !== undefined) {
      return metaFlag
    }
  }

  return false
}

export function useChartHighlight(chartId: string, shouldHighlight: boolean) {
  const { highlightedChartId, setHighlightedChartId } = useSharedContext()

  useEffect(() => {
    if (!shouldHighlight) {
      return
    }
    setHighlightedChartId(chartId)
    return () => {
      setHighlightedChartId((current) => (current === chartId ? null : current))
    }
  }, [chartId, shouldHighlight, setHighlightedChartId])

  const dismiss = useCallback(() => {
    setHighlightedChartId((current) => (current === chartId ? null : current))
  }, [chartId, setHighlightedChartId])

  useEffect(() => {
    if (highlightedChartId !== chartId) {
      return
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        dismiss()
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => {
      window.removeEventListener("keydown", handleKeyDown)
    }
  }, [chartId, highlightedChartId, dismiss])

  return {
    isHighlighted: highlightedChartId === chartId,
    dismiss,
  }
}
