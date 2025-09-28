import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
import OpenAI from "openai";

const azureOpenAIApiKey = process.env.AZURE_OPENAI_API_KEY;
const azureOpenAIInstance = process.env.AZURE_OPENAI_INSTANCE;
const azureOpenAIDeployment = process.env.AZURE_OPENAI_DEPLOYMENT;
const azureOpenAIEndpoint =
  process.env.AZURE_OPENAI_ENDPOINT ??
  (azureOpenAIInstance ? `https://${azureOpenAIInstance}.openai.azure.com` : undefined);
const azureOpenAIApiVersion = process.env.AZURE_OPENAI_API_VERSION ?? "2024-04-01-preview";

if (!azureOpenAIApiKey) {
  throw new Error("Missing AZURE_OPENAI_API_KEY environment variable.");
}

if (!azureOpenAIEndpoint) {
  throw new Error(
    "Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_INSTANCE environment variable.",
  );
}

if (!azureOpenAIDeployment) {
  throw new Error("Missing AZURE_OPENAI_DEPLOYMENT environment variable.");
}

const normalizedAzureEndpoint = azureOpenAIEndpoint.replace(/\/+$/, "");
const backendBaseUrl = process.env.PY_BACKEND_URL || "http://localhost:8004";

const openai = new OpenAI({
  apiKey: azureOpenAIApiKey,
  baseURL: `${normalizedAzureEndpoint}/openai/deployments/${azureOpenAIDeployment}`,
  defaultQuery: { "api-version": azureOpenAIApiVersion },
  defaultHeaders: { "api-key": azureOpenAIApiKey },
});

const serviceAdapter = new OpenAIAdapter({
  openai,
  model: azureOpenAIDeployment,
});

const runtime = new CopilotRuntime({
  actions: () => [
    {
      name: "searchInternet",
      description:
        "Searches the internet for current information using the FastAPI Tavily integration.",
      parameters: [
        {
          name: "query",
          type: "string",
          description: "The query to search the internet for.",
          required: true,
        },
      ],
      handler: async ({ query }: { query: string }) => {
        const response = await fetch(`${backendBaseUrl}/actions/search-internet`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query }),
        });

        if (!response.ok) {
          const message = await response.text();
          throw new Error(`searchInternet failed (${response.status}): ${message}`);
        }

        const data = (await response.json()) as { results: string };
        return data.results;
      },
    },
    {
      name: "analyzeDashboardWithPydanticAI",
      description:
        "Uses the FastAPI PydanticAI service to analyse dashboard metrics. Provide the user question along with any key numbers you already know.",
      parameters: [
        {
          name: "question",
          type: "string",
          description: "The question or analysis request to forward to the PydanticAI agent.",
          required: true,
        },
      ],
      handler: async ({ question }: { question: string }) => {
        const response = await fetch(`${backendBaseUrl}/actions/analyze-dashboard`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
        });

        if (!response.ok) {
          const message = await response.text();
          throw new Error(`analyzeDashboardWithPydanticAI failed (${response.status}): ${message}`);
        }

        const data = (await response.json()) as { answer: string };
        return data.answer;
      },
    },
  ],
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};

