/** Utility helpers for Markdown rendering in the dashboard UI. */

export function normalizeMarkdownTables(markdown: string): string {
  if (!markdown || markdown.indexOf("|") === -1) {
    return markdown;
  }

  const rowBoundaryPattern = /\|\s+\|/g;
  const inlineRowPattern = /(^|[^|\n])\s(\|[^\n|]+(?:\|[^\n|]+)+\|?)/g;

  let normalized = markdown.replace(rowBoundaryPattern, "|\n|");
  normalized = normalized.replace(inlineRowPattern, (_match, prefix: string, row: string) => {
    const trimmedRow = row.trim();
    if (!prefix) {
      return trimmedRow;
    }
    return `${prefix}\n${trimmedRow}`;
  });

  return normalized;
}
