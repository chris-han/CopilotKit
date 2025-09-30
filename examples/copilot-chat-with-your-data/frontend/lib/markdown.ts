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

  return normalizedLines.join("\n");
}
