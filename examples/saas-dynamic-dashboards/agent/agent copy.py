"""Pydantic AI implementation of the testing agent."""

from __future__ import annotations

import os
from textwrap import dedent
from typing import Literal

from dotenv import load_dotenv
from ag_ui.core import EventType, StateSnapshotEvent
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.ag_ui import StateDeps
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

load_dotenv()


class TestCase(BaseModel):
    """Represents a single test case inside a suite."""

    id: str
    name: str
    status: Literal["passed", "failed", "idle", "pending", "in_progress"]
    executionTime: str
    createdAt: str
    updatedAt: str
    environment: str
    browser: str | None = None
    device: str | None = None
    testSteps: list[str]
    failureReason: str | None = None


class TestSuite(BaseModel):
    """High level grouping of related test cases."""

    testId: str
    prId: str
    title: str
    status: Literal["passed", "failed", "idle", "in_progress"]
    shortDescription: str
    testCases: list[TestCase]
    totalTestCases: int
    passedTestCases: int
    failedTestCases: int
    skippedTestCases: int
    coverage: float
    createdAt: str
    updatedAt: str
    executedBy: str


class TestScriptsPayload(BaseModel):
    """Payload emitted by the generate_test_scripts tool."""

    testSuites: list[TestSuite] = Field(default_factory=list)


class AgentState(BaseModel):
    """State tracked for the testing agent."""

    testScripts: TestScriptsPayload | None = None


AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-04-01-preview")

if not AZURE_OPENAI_API_KEY:
    raise ValueError("Missing AZURE_OPENAI_API_KEY environment variable")
if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("Missing AZURE_OPENAI_ENDPOINT environment variable")
if not AZURE_OPENAI_DEPLOYMENT:
    raise ValueError("Missing AZURE_OPENAI_DEPLOYMENT environment variable")

normalized_endpoint = AZURE_OPENAI_ENDPOINT.rstrip("/")
azure_provider = AzureProvider(
    azure_endpoint=normalized_endpoint,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
)

agent = Agent(
    model=OpenAIChatModel(model_name=AZURE_OPENAI_DEPLOYMENT, provider=azure_provider),
    deps_type=StateDeps[AgentState],
)

try:
    app = agent.to_ag_ui(name="testing_agent", deps=StateDeps(AgentState()))
except TypeError:  # pragma: no cover - for older pydantic-ai releases
    app = agent.to_ag_ui(deps=StateDeps(AgentState()))


@agent.instructions
async def testing_instructions(ctx: RunContext[StateDeps[AgentState]]) -> str:
    """System prompt for the testing agent."""

    prior_scripts = "No previously generated scripts."
    if ctx.deps.state.testScripts:
        prior_scripts = ctx.deps.state.testScripts.model_dump_json(indent=2)

    return dedent(
        f"""
        You are a helpful assistant that can perform any task related to software testing and PR validation.
        When the user requests help with testing you MUST call the `generate_test_scripts` tool exactly once
        before providing your final response.

        After the tool runs, craft a concise summary (maximum of five sentences) of the generated suites and
        remind the user that you can add suites to their testing list if requested. Never list the full suites
        inline in the summary—just the highlights.

        Every time you generate scripts you MUST return 4 DISTINCT TEST SUITES. Each suite must:
        - Align with the PR context or CopilotKit readable content provided by the user.
        - Contain unique test cases and metadata with realistic timestamps, coverage, and ownership details.
        - Use any user emails exactly as presented in the provided context.

        Current cached test scripts state:
        {prior_scripts}
        """
    )


@agent.tool
async def generate_test_scripts(
    ctx: RunContext[StateDeps[AgentState]], payload: TestScriptsPayload
) -> StateSnapshotEvent:
    """Capture the generated test suites and expose them to the frontend."""

    ctx.deps.state.testScripts = payload
    return StateSnapshotEvent(
        type=EventType.STATE_SNAPSHOT,
        snapshot=ctx.deps.state,
    )


def main() -> None:
    """Run the uvicorn server."""

    port = int(os.getenv("PORT", "8006"))
    from uvicorn import run

    run("agent:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    main()
