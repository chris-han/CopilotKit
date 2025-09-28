import { prData } from "@/lib/data";
import testData from "@/lib/testData";
import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import OpenAI from "openai";

import { NextRequest } from "next/server";

const {
  AZURE_OPENAI_API_KEY,
  AZURE_OPENAI_ENDPOINT,
  AZURE_OPENAI_DEPLOYMENT,
  AZURE_OPENAI_API_VERSION = "2024-04-01-preview",
} = process.env;

if (!AZURE_OPENAI_API_KEY) {
  throw new Error("Missing AZURE_OPENAI_API_KEY environment variable");
}
if (!AZURE_OPENAI_ENDPOINT) {
  throw new Error("Missing AZURE_OPENAI_ENDPOINT environment variable");
}
if (!AZURE_OPENAI_DEPLOYMENT) {
  throw new Error("Missing AZURE_OPENAI_DEPLOYMENT environment variable");
}

const normalizedAzureEndpoint = AZURE_OPENAI_ENDPOINT.replace(/\/+$/, "");

const serviceAdapter = new OpenAIAdapter({
  openai: new OpenAI({
    apiKey: AZURE_OPENAI_API_KEY,
    baseURL: `${normalizedAzureEndpoint}/openai/deployments/${AZURE_OPENAI_DEPLOYMENT}`,
    defaultQuery: { "api-version": AZURE_OPENAI_API_VERSION },
    defaultHeaders: { "api-key": AZURE_OPENAI_API_KEY },
  }),
  model: AZURE_OPENAI_DEPLOYMENT,
  // Azure OpenAI still expects the traditional `system` role. Keeping the
  // original role ensures the model consistently honors the forced tool calls.
  keepSystemRole: true,
});

export const POST = async (req: NextRequest) => {
  // console.log("req", req);
  const runtime = new CopilotRuntime({
    actions: ({ properties, url }) => {
      return [
        {
          name: "fetchData_allPRData",
          description: `Data fetching action that fetches all the PR data from the database.
          
The PR data structure includes:
- id: Unique PR identifier (e.g., 'PR01')
- title: PR title
- status: Current status ('approved', 'needs_revision', 'merged', 'in_review')
- assignedReviewer: Email of the assigned reviewer
- assignedTester: Email of the assigned tester
- daysSinceStatusChange: Number of days since last status change
- createdAt: ISO timestamp of creation
- updatedAt: ISO timestamp of last update
- userId: Numeric user ID
- author: Email of the PR author
- repository: Repository name
- branch: Branch name

Example PR data:
{
  "id": "PR01324",
  "title": "Implement user authentication flow",
  "status": "approved",
  "assignedReviewer": "johnknfjsg.doe@got.com",
  "assignedTester": "janjnglkrfe.smith@got.com",
  "daysSinceStatusChange": 2,
  "createdAt": "2025-04-28T14:06:36.848Z",
  "updatedAt": "2025-04-29T00:46:50.492Z",
  "userId": 1,
  "author": "Jon.snnrfmlkgow@got.com",
  "repository": "frontend",
  "branch": "feature/auth-flow"
}`,
          parameters: [],
          handler: async () => {
            return prData;
          },
        },
        {
          name: "fetchData_PRDataByUserId",
          description: `Data fetching action that filters PR data based on userId parameter.          
            The PR data structure includes:
            - id: Unique PR identifier (e.g., 'PR01')
            - title: PR title
            - status: Current status ('approved', 'needs_revision', 'merged', 'in_review')
            - assignedReviewer: Email of the assigned reviewer
            - assignedTester: Email of the assigned tester
            - daysSinceStatusChange: Number of days since last status change
            - createdAt: ISO timestamp of creation
            - updatedAt: ISO timestamp of last update
            - userId: Numeric user ID
            - author: Email of the PR author
            - repository: Repository name
            - branch: Branch name

            Example PR data:
            {
              "id": "PR01hkfdiugo",
              "title": "Implement user authentication flow",
              "status": "approved",
              "assignedReviewer": "johhgtuyhion.doe@got.com",
              "assignedTester": "janeafsdg.smith@got.com",
              "daysSinceStatusChange": 2,
              "createdAt": "2025-04-28T14:06:36.848Z",
              "updatedAt": "2025-04-29T00:46:50.492Z",
              "userId": 1,
              "author": "Jon.sfdgsnow@got.com",
              "repository": "frontend",
              "branch": "feature/auth-flow"
          }`,
          parameters: [
            {
              name: "userId",
              type: "number",
              description: "The user ID to filter PRs by"
            }
          ],
          handler: async ({ userId }: { userId: number }) => {
            return prData.filter(pr => pr.userId === userId);
          }
        },
        {
          name: "fetchData_AuthorNames",
          description: `Data fetching action that gets all the unique author names from the PR data.          
            The PR data structure includes:
            - id: Unique PR identifier (e.g., 'PR01')
            - title: PR title
            - status: Current status ('approved', 'needs_revision', 'merged', 'in_review')
            - assignedReviewer: Email of the assigned reviewer
            - assignedTester: Email of the assigned tester
            - daysSinceStatusChange: Number of days since last status change
            - createdAt: ISO timestamp of creation
            - updatedAt: ISO timestamp of last update
            - userId: Numeric user ID
            - author: Email of the PR author
            - repository: Repository name
            - branch: Branch name

            Example PR data:
            {
              "id": "PR0asdas1",
              "title": "Implement user authentication flow",
              "status": "approved",
              "assignedReviewer": "johafsdkhoin.doe@got.com",
              "assignedTester": "jaakdsjfogne.smith@got.com",
              "daysSinceStatusChange": 2,
              "createdAt": "2025-04-28T14:06:36.848Z",
              "updatedAt": "2025-04-29T00:46:50.492Z",
              "userId": 1,
              "author": "Jon.snadsljfkoow@got.com",
              "repository": "frontend",
              "branch": "feature/auth-flow"
          }`,
          parameters: [],
          handler: async () => {
            let authorNames = prData.map(pr => pr.author);
            let uniqueAuthorNames = [...new Set(authorNames)];
            console.log(uniqueAuthorNames, "uniqueAuthorNames");            
            return uniqueAuthorNames;
          }
        },
        {
          name: "fetchData_ReviewerNames",
          description: `Data fetching action that gets all the unique reviewer names from the PR data.          
            The PR data structure includes:
            - id: Unique PR identifier (e.g., 'PR01')
            - title: PR title
            - status: Current status ('approved', 'needs_revision', 'merged', 'in_review')
            - assignedReviewer: Email of the assigned reviewer
            - assignedTester: Email of the assigned tester
            - daysSinceStatusChange: Number of days since last status change
            - createdAt: ISO timestamp of creation
            - updatedAt: ISO timestamp of last update
            - userId: Numeric user ID
            - author: Email of the PR author
            - repository: Repository name
            - branch: Branch name

            Example PR data:
            {
              "id": "PR99",
              "title": "Implement user authentication flow",
              "status": "approved",
              "assignedReviewer": "johnasd.doe@got.com",
              "assignedTester": "jane.smitasdasdh@got.com",
              "daysSinceStatusChange": 2,
              "createdAt": "2025-04-28T14:06:36.848Z",
              "updatedAt": "2025-04-29T00:46:50.492Z",
              "userId": 1,
              "author": "Jon.asdfsadfsnow@got.com",
              "repository": "frontend",
              "branch": "feature/auth-flow"
          }`,
          parameters: [],
          handler: async () => {
            let reviewerNames = prData.map(pr => pr.assignedReviewer);
            let uniqueReviewerNames = [...new Set(reviewerNames)];
            console.log(uniqueReviewerNames, "uniqueReviewerNames");            
            return uniqueReviewerNames;
          }
        },
        {
          name: "fetchData_TesterNames",
          description: `Data fetching action that gets all the unique tester names from the Tests data.          
            The Tests data structure includes:
            - testId: Unique test identifier (e.g., 'TEST001')
            - prId: Associated PR identifier (e.g., 'PR01')
            - title: Test suite title
            - status: Current status ('passed', 'failed', 'idle', 'running')
            - testCases: Array of test cases, each containing:
              - id: Test case identifier (e.g., 'TC001-1')
              - name: Test case name
              - status: Test case status
              - executionTime: Time taken to execute
              - createdAt: ISO timestamp of creation
              - updatedAt: ISO timestamp of last update
              - environment: Test environment
              - browser: Browser used
              - testSteps: Array of test steps
            - totalTestCases: Total number of test cases
            - passedTestCases: Number of passed test cases
            - failedTestCases: Number of failed test cases
            - skippedTestCases: Number of skipped test cases
            - coverage: Test coverage percentage
            - createdAt: ISO timestamp of test suite creation
            - updatedAt: ISO timestamp of last update
            - executedBy: Email of the tester who executed the tests

            Example Test data:
            {
              "testId": "TEST69",
              "prId": "PR81",
              "title": "User Authentication Flow Test Suite",
              "status": "passed",
              "testCases": [
                {
                  "id": "TC001-1",
                  "name": "Login with valid credentials",
                  "status": "passed",
                  "executionTime": "1.2s",
                  "createdAt": "2025-04-28T15:00:00.000Z",
                  "updatedAt": "2025-04-28T15:05:00.000Z",
                  "environment": "staging",
                  "browser": "Chrome",
                  "testSteps": [
                    "Enter valid email",
                    "Enter valid password",
                    "Click login button",
                    "Verify successful login"
                  ]
                }
              ],
              "totalTestCases": 3,
              "passedTestCases": 3,
              "failedTestCases": 0,
              "skippedTestCases": 0,
              "coverage": 85,
              "createdAt": "2025-04-28T14:30:00.000Z",
              "updatedAt": "2025-04-28T15:30:00.000Z",
              "executedBy": "jane.smith@got.com"
            }`,
          parameters: [],
          handler: async () => {
            let testerNames = testData.map(test => test.executedBy);
            let uniqueTesterNames = [...new Set(testerNames)];
            console.log(uniqueTesterNames, "uniqueTesterNames");            
            return uniqueTesterNames;
          }
        },
        {
          name: "fetchData_AverageReviewTimeByStatus",
          description: `Aggregates PR review durations by status. The review duration is the time difference between createdAt and updatedAt for each PR. Returns an object with an overall summary and optional repository-level breakdown.

Response format:
{
  "overall": [
    {
      "status": "approved",
      "averageReviewTimeHours": 26.5,
      "averageReviewTimeDays": 1.1,
      "prCount": 4
    }
  ],
  "byRepository": [
    {
      "repository": "frontend",
      "status": "approved",
      "averageReviewTimeHours": 24.2,
      "averageReviewTimeDays": 1.0,
      "prCount": 2
    }
  ]
}

Use the "overall" array to render quick comparisons by status. Include "byRepository" when deeper analysis is needed.`,
          parameters: [],
          handler: async () => {
            const millisecondsToHours = (ms: number) => ms / (1000 * 60 * 60);
            const hoursToDays = (hours: number) => hours / 24;

            const prByStatus = prData.reduce<Record<string, typeof prData>>((acc, pr) => {
              const statusKey = pr.status?.toLowerCase() ?? "unknown";
              if (!acc[statusKey]) {
                acc[statusKey] = [];
              }
              acc[statusKey].push(pr);
              return acc;
            }, {});

            const computeAverage = (prs: typeof prData) => {
              if (!prs.length) {
                return {
                  averageReviewTimeHours: 0,
                  averageReviewTimeDays: 0,
                };
              }

              const totalHours = prs.reduce((sum, pr) => {
                const created = new Date(pr.createdAt).getTime();
                const updated = new Date(pr.updatedAt).getTime();
                const durationMs = Math.max(updated - created, 0);
                return sum + millisecondsToHours(durationMs);
              }, 0);

              const averageHours = totalHours / prs.length;

              return {
                averageReviewTimeHours: Number(averageHours.toFixed(2)),
                averageReviewTimeDays: Number(hoursToDays(averageHours).toFixed(2)),
              };
            };

            const overall = Object.entries(prByStatus).map(([status, prs]) => {
              const averages = computeAverage(prs);
              return {
                status,
                prCount: prs.length,
                ...averages,
              };
            });

            overall.sort((a, b) => a.status.localeCompare(b.status));

            const byRepository: Array<{
              repository: string;
              status: string;
              prCount: number;
              averageReviewTimeHours: number;
              averageReviewTimeDays: number;
            }> = [];

            for (const [status, prs] of Object.entries(prByStatus)) {
              const groupedByRepo = prs.reduce<Record<string, typeof prData>>((acc, pr) => {
                const repoKey = pr.repository ?? "unknown";
                if (!acc[repoKey]) {
                  acc[repoKey] = [];
                }
                acc[repoKey].push(pr);
                return acc;
              }, {});

              for (const [repository, repoPrs] of Object.entries(groupedByRepo)) {
                const averages = computeAverage(repoPrs);
                byRepository.push({
                  repository,
                  status,
                  prCount: repoPrs.length,
                  ...averages,
                });
              }
            }

            byRepository.sort((a, b) => {
              const statusCompare = a.status.localeCompare(b.status);
              return statusCompare === 0 ? a.repository.localeCompare(b.repository) : statusCompare;
            });

            return {
              generatedAt: new Date().toISOString(),
              overall,
              byRepository,
            };
          },
        }
      ] as any
    },
    agents: {
      testing_agent: new HttpAgent({
        url: process.env.REMOTE_AGENT_URL || "http://localhost:8006/",
      }),
    },
  });
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
