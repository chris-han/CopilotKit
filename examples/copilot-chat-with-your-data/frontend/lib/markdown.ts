/** Utility helpers for Markdown rendering in the dashboard UI. */

export function normalizeMarkdownTables(markdown: string): string {
  if (!markdown || markdown.indexOf("|") === -1) {
    return markdown;
  }

  let rebuilt = "";
  let pipesInRow = 0;

  for (let index = 0; index < markdown.length; index += 1) {
    const char = markdown[index];

    if (char === "\n") {
      pipesInRow = 0;
      rebuilt += char;
      continue;
    }

    rebuilt += char;

    if (char !== "|") {
      continue;
    }

    pipesInRow += 1;

    let lookahead = index + 1;
    while (lookahead < markdown.length && (markdown[lookahead] === " " || markdown[lookahead] === "\t")) {
      lookahead += 1;
    }

    const nextSignificantChar = markdown[lookahead];
    const shouldBreakRow = pipesInRow >= 3 && nextSignificantChar === "|";

    if (!shouldBreakRow) {
      continue;
    }

    rebuilt += "\n";
    pipesInRow = 0;
    index = lookahead - 1;
  }

  const normalizedLines: string[] = [];

  for (const line of rebuilt.split("\n")) {
    if (!line.includes("|")) {
      normalizedLines.push(line);
      continue;
    }

    const trimmedStart = line.trimStart();
    if (!trimmedStart) {
      normalizedLines.push(line);
      continue;
    }

    if (trimmedStart.startsWith("|")) {
      normalizedLines.push(trimmedStart.replace(/[ \t]+$/g, ""));
      continue;
    }

    normalizedLines.push(line);
  }

  const withHeaderSeparators: string[] = [];

  for (let lineIndex = 0; lineIndex < normalizedLines.length; lineIndex += 1) {
    const line = normalizedLines[lineIndex];
    withHeaderSeparators.push(line);

    if (!isLikelyTableRow(line)) {
      continue;
    }

    const previousLine = normalizedLines[lineIndex - 1];
    if (previousLine && isLikelyTableRow(previousLine) && !isTableSeparatorRow(previousLine)) {
      continue;
    }

    const nextLine = normalizedLines[lineIndex + 1];
    if (!nextLine || !isLikelyTableRow(nextLine) || isTableSeparatorRow(nextLine)) {
      continue;
    }

    const columnCount = getTableColumnCount(line);
    if (columnCount < 2) {
      continue;
    }

    const leadingWhitespaceMatch = line.match(/^\s*/);
    const leadingWhitespace = leadingWhitespaceMatch ? leadingWhitespaceMatch[0] : "";
    const separatorCells = Array(columnCount).fill("---");
    const separatorRow = `${leadingWhitespace}| ${separatorCells.join(" | ")} |`;

    withHeaderSeparators.push(separatorRow);
  }

  return withHeaderSeparators.join("\n");
}

function isLikelyTableRow(line: string): boolean {
  const trimmed = line.trim();
  if (!trimmed || !trimmed.startsWith("|")) {
    return false;
  }

  return getTableColumnCount(line) >= 2;
}

function isTableSeparatorRow(line: string): boolean {
  if (!isLikelyTableRow(line)) {
    return false;
  }

  const cells = extractTableCells(line);
  if (cells.length === 0) {
    return false;
  }

  return cells.every((cell) => /^:?[-]{3,}:?$/.test(cell));
}

function getTableColumnCount(line: string): number {
  const trimmed = line.trim();
  if (!trimmed.includes("|")) {
    return 0;
  }

  const segments = trimmed.split("|");
  const startIndex = trimmed.startsWith("|") ? 1 : 0;
  const endIndex = trimmed.endsWith("|") ? segments.length - 1 : segments.length;
  return Math.max(endIndex - startIndex, 0);
}

function extractTableCells(line: string): string[] {
  const trimmed = line.trim();
  if (!trimmed.startsWith("|")) {
    return [];
  }

  const segments = trimmed.split("|");
  const startIndex = trimmed.startsWith("|") ? 1 : 0;
  const endIndex = trimmed.endsWith("|") ? segments.length - 1 : segments.length;
  const cells: string[] = [];

  for (let index = startIndex; index < endIndex; index += 1) {
    cells.push(segments[index].trim());
  }

  return cells;
}
