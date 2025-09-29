/** Utility helpers for Markdown rendering in the dashboard UI. */

export function normalizeMarkdownTables(markdown: string): string {
  if (!markdown || markdown.indexOf("|") === -1) {
    return markdown;
  }

  const rowBoundaryPattern = /\|\s+\|/g;
  const rowStartPattern = /([^\n])(\|[^\n|]+(?:\|[^\n|]+){2,}\|?)/g;

  let normalized = markdown.replace(rowBoundaryPattern, "|\n|");
  normalized = normalized.replace(rowStartPattern, (_, prefix: string, row: string) => {
    return `${prefix}\n${row.trimStart()}`;
  });

  return normalized;
}
