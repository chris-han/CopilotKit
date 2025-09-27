const DEFAULT_BASE_URL = "https://api.tavily.com";
const DEFAULT_TIMEOUT_MS = 60_000;

type TavilyClientConfig = {
  apiKey?: string | null;
  baseUrl?: string;
  timeoutMs?: number;
};

type TavilySearchOptions = {
  max_results?: number;
  search_depth?: "basic" | "advanced";
};

type TavilySearchRequest = {
  query: string;
  max_results?: number;
  search_depth?: "basic" | "advanced";
};

type TavilySearchResponse = Record<string, unknown>;

function ensureApiKey(apiKey?: string | null): string {
  if (apiKey && apiKey.trim().length > 0) {
    return apiKey;
  }

  throw new Error("Missing TAVILY_API_KEY environment variable.");
}

function normalizeBaseUrl(baseUrl?: string): string {
  const url = baseUrl?.trim() || DEFAULT_BASE_URL;
  return url.replace(/\/+$/, "");
}

async function postJson<T>(
  url: string,
  apiKey: string,
  body: TavilySearchRequest,
  timeoutMs: number,
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), Math.max(timeoutMs, 0));

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Tavily request failed with status ${response.status}: ${errorText}`,
      );
    }

    return (await response.json()) as T;
  } catch (error) {
    if ((error as Error).name === "AbortError") {
      throw new Error("Tavily request timed out");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export function createTavilyClient({
  apiKey,
  baseUrl,
  timeoutMs = DEFAULT_TIMEOUT_MS,
}: TavilyClientConfig = {}) {
  const resolvedKey = ensureApiKey(apiKey ?? process.env.TAVILY_API_KEY);
  const resolvedBaseUrl = normalizeBaseUrl(baseUrl ?? process.env.TAVILY_BASE_URL);

  return {
    async search(query: string, options: TavilySearchOptions = {}) {
      const payload: TavilySearchRequest = {
        query,
        max_results: options.max_results ?? 5,
        search_depth: options.search_depth ?? "basic",
      };

      return postJson<TavilySearchResponse>(
        `${resolvedBaseUrl}/search`,
        resolvedKey,
        payload,
        timeoutMs,
      );
    },
  };
}

export type TavilyClient = ReturnType<typeof createTavilyClient>;
export type { TavilySearchOptions, TavilySearchResponse };
