import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from '@copilotkit/runtime';

import { NextRequest } from 'next/server';
import OpenAI from 'openai';
import { createTavilyClient } from '@/lib/tavily';

const azureOpenAIApiKey = process.env.AZURE_OPENAI_API_KEY;
const azureOpenAIInstance = process.env.AZURE_OPENAI_INSTANCE;
const azureOpenAIDeployment = process.env.AZURE_OPENAI_DEPLOYMENT;
const azureOpenAIEndpoint =
  process.env.AZURE_OPENAI_ENDPOINT ??
  (azureOpenAIInstance ? `https://${azureOpenAIInstance}.openai.azure.com` : undefined);
const azureOpenAIApiVersion = process.env.AZURE_OPENAI_API_VERSION ?? '2024-04-01-preview';

if (!azureOpenAIApiKey) {
  throw new Error('Missing AZURE_OPENAI_API_KEY environment variable.');
}

if (!azureOpenAIEndpoint) {
  throw new Error('Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_INSTANCE environment variable.');
}

if (!azureOpenAIDeployment) {
  throw new Error('Missing AZURE_OPENAI_DEPLOYMENT environment variable.');
}

const normalizedAzureEndpoint = azureOpenAIEndpoint.replace(/\/+$/, '');

const openai = new OpenAI({
  apiKey: azureOpenAIApiKey,
  baseURL: `${normalizedAzureEndpoint}/openai/deployments/${azureOpenAIDeployment}`,
  defaultQuery: { 'api-version': azureOpenAIApiVersion },
  defaultHeaders: { 'api-key': azureOpenAIApiKey },
});
const serviceAdapter = new OpenAIAdapter({
  openai,
  model: azureOpenAIDeployment,
});
const runtime = new CopilotRuntime({
  actions: () => {
    return [
      {
        name: "searchInternet",
        description: "Searches the internet for information.",
        parameters: [
          {
            name: "query",
            type: "string",
            description: "The query to search the internet for.",
            required: true,
          },
        ],
        handler: async ({ query }: { query: string }) => {
          const tavilyClient = createTavilyClient({
            apiKey: process.env.TAVILY_API_KEY,
          });

          return await tavilyClient.search(query, { max_results: 5 });
        },
      },
    ]
  }
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: '/api/copilotkit',
  });

  return handleRequest(req);
};
