# Chat with your data

Transform your data visualization experience with an AI-powered dashboard assistant. Ask questions about your data in natural language, get insights, and interact with your metrics—all through a conversational interface powered by the AG-UI protocol and a Pydantic AI backend.

[Click here for a running example](https://chat-with-your-data.vercel.app/)

<div align="center">
  <img src="./preview.gif" alt="Chat with your data"/>
  <a href="https://nextjs.org" target="_blank">
    <img src="https://img.shields.io/badge/Built%20with-Next.js%2015-black" alt="Built with Next.js"/>
  </a>
  <a href="https://ui.shadcn.com/" target="_blank">
    <img src="https://img.shields.io/badge/Styled%20with-shadcn%2Fui-black" alt="Styled with shadcn/ui"/>
  </a>
</div>

## 🛠️ Getting Started

### Prerequisites

- Node.js 18+ 
- npm, yarn, or pnpm

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/CopilotKit/CopilotKit.git
   cd CopilotKit/examples/copilot-chat-with-your-data
   ```

2. Install dependencies:

   ```bash
   pnpm install
   ```

   <details>
     <summary><b>Using other package managers</b></summary>
     
     ```bash
     # Using yarn
     yarn install
     
     # Using npm
     npm install
     ```
   </details>

3. Create a `.env` file in the project root and add your [Azure OpenAI](https://learn.microsoft.com/azure/ai-services/openai/overview) and [Tavily](https://tavily.com/api-key) credentials:
   ```
   AZURE_OPENAI_API_KEY=your_azure_openai_key
   # Provide either the resource endpoint (preferred) or instance name.
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
   # AZURE_OPENAI_INSTANCE=your_resource_instance
   AZURE_OPENAI_DEPLOYMENT=your_deployment_name
   # Optional: override the default API version (defaults to 2024-04-01-preview)
   # AZURE_OPENAI_API_VERSION=2024-02-15-preview
   TAVILY_API_KEY=your_tavily_api_key
   # Optional: override the AG-UI runtime URL consumed by the Next.js app
   # NEXT_PUBLIC_AG_UI_RUNTIME_URL=http://localhost:8004/ag-ui/run
   ```

4. Install backend dependencies and start the FastAPI runtime in a separate terminal:

   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8004
   ```

5. Start the Next.js development server:

   ```bash
   pnpm dev
   ```

   <details>
     <summary><b>Using other package managers</b></summary>
     
     ```bash
     # Using yarn
     yarn dev
     
     # Using npm
     npm run dev
     ```
   </details>

6. Open [http://localhost:3000](http://localhost:3000) in your browser to see the application.

## 🧩 How It Works

### AG-UI Provider
`AgUiProvider` establishes a shared AG-UI `HttpAgent`, streams protocol events, and seeds the conversation with the system prompt. The provider wraps the entire Next.js layout so every client component can access the chat state.

<em>[app/layout.tsx](./app/layout.tsx)</em>

```tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  const runtimeUrl = process.env.NEXT_PUBLIC_AG_UI_RUNTIME_URL ?? "http://localhost:8004/ag-ui/run";

  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <AgUiProvider runtimeUrl={runtimeUrl}>{children}</AgUiProvider>
      </body>
    </html>
  );
}
```

### Sidebar Chat Interface
`AgUiSidebar` renders the conversational UI, streams assistant responses, displays loading states, and reacts to custom highlight events to sync with the dashboard visualizations.

<em>[components/ag-ui/AgUiSidebar.tsx](./components/ag-ui/AgUiSidebar.tsx)</em>

```tsx
const { messages, sendMessage, isRunning } = useAgUiAgent();

return (
  <aside className="fixed right-0 top-0 h-full w-full max-w-md bg-white">
    {/* ... */}
    <div className="flex-1 overflow-y-auto">
      {messages.map((message) =>
        message.role === "assistant" ? (
          <AssistantMessage key={message.id} content={message.content} isStreaming={message.pending} />
        ) : (
          <div key={message.id} className="self-end ml-auto bg-blue-600 text-white px-3 py-2 rounded-lg">
            {message.content}
          </div>
        ),
      )}
    </div>
    <form onSubmit={handleSubmit}>{/* composer */}</form>
  </aside>
);
```

### FastAPI Runtime
The FastAPI backend bridges AG-UI events with a Pydantic AI agent. Each request to `/ag-ui/run` is validated against the AG-UI protocol, streamed as Server-Sent Events, and augmented with custom `chart.highlight` events so the frontend can coordinate card highlights.

<em>[backend/main.py](./backend/main.py)</em>

```py
async def _agent_event_stream(run_input: RunAgentInput) -> AsyncIterator[str]:
    thread_id = run_input.thread_id or f"thread-{uuid4()}"
    run_id = run_input.run_id or f"run-{uuid4()}"

    yield encoder.encode(RunStartedEvent(type=EventType.RUN_STARTED, thread_id=thread_id, run_id=run_id))

    answer = await _run_analysis(latest_user, system_messages, transcript)
    sanitized_answer, chart_ids = _separate_highlight_directives(answer)

    yield encoder.encode(TextMessageStartEvent(type=EventType.TEXT_MESSAGE_START, message_id=message_id, role="assistant"))
    yield encoder.encode(TextMessageContentEvent(type=EventType.TEXT_MESSAGE_CONTENT, message_id=message_id, delta=sanitized_answer))
    yield encoder.encode(TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=message_id))

    for chart_id in chart_ids:
        yield encoder.encode(CustomEvent(type=EventType.CUSTOM, name="chart.highlight", value={"chartId": chart_id}))

    yield encoder.encode(RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=thread_id, run_id=run_id))
```

## 📚 Learn More

- [AG-UI Protocol Documentation](https://github.com/ag-ui-protocol/ag-ui) – Protocol concepts, SDK usage, and reference integrations.
- [Pydantic AI](https://ai.pydantic.dev/) – Build structured agents in Python with tool support and schema validation.
