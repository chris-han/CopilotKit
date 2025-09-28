/**
 * Type definitions distilled from `@copilotkit/runtime-client-gql`.
 * These mirror the GraphQL schema used by CopilotKit's runtime so
 * both the FastAPI backend and the React client can share a single
 * source of truth for message and response shapes.
 */

export type ISODateString = string;

export interface BaseMessageStatus {
  code: MessageStatusCode;
}

export interface FailedMessageStatus extends BaseMessageStatus {
  code: MessageStatusCode.Failed;
  reason: string;
}

export interface PendingMessageStatus extends BaseMessageStatus {
  code: MessageStatusCode.Pending;
}

export interface SuccessMessageStatus extends BaseMessageStatus {
  code: MessageStatusCode.Success;
}

export type MessageStatus =
  | FailedMessageStatus
  | PendingMessageStatus
  | SuccessMessageStatus;

export interface BaseMessageOutput {
  id: string;
  createdAt: ISODateString;
  status: MessageStatus;
}

export enum MessageRole {
  Assistant = "assistant",
  Developer = "developer",
  System = "system",
  Tool = "tool",
  User = "user",
}

export interface TextMessageOutput extends BaseMessageOutput {
  __typename: "TextMessageOutput";
  content: string[];
  role: MessageRole;
  parentMessageId?: string | null;
}

export interface ImageMessageOutput extends BaseMessageOutput {
  __typename: "ImageMessageOutput";
  format: string;
  bytes: string;
  role: MessageRole;
  parentMessageId?: string | null;
}

export interface ActionExecutionMessageOutput extends BaseMessageOutput {
  __typename: "ActionExecutionMessageOutput";
  name: string;
  arguments: string[];
  parentMessageId?: string | null;
}

export interface ResultMessageOutput extends BaseMessageOutput {
  __typename: "ResultMessageOutput";
  actionExecutionId: string;
  actionName: string;
  result: string;
}

export interface AgentStateMessageOutput extends BaseMessageOutput {
  __typename: "AgentStateMessageOutput";
  agentName: string;
  nodeName: string;
  runId: string;
  threadId: string;
  running: boolean;
  active: boolean;
  role: MessageRole;
  state: string;
}

export type CopilotMessageOutput =
  | TextMessageOutput
  | ImageMessageOutput
  | ActionExecutionMessageOutput
  | ResultMessageOutput
  | AgentStateMessageOutput;

export enum ResponseStatusCode {
  Failed = "Failed",
  Pending = "Pending",
  Success = "Success",
}

export interface BaseResponseStatus {
  code: ResponseStatusCode;
}

export interface FailedResponseStatus extends BaseResponseStatus {
  code: ResponseStatusCode.Failed;
  reason: string;
  details?: unknown;
}

export interface PendingResponseStatus extends BaseResponseStatus {
  code: ResponseStatusCode.Pending;
}

export interface SuccessResponseStatus extends BaseResponseStatus {
  code: ResponseStatusCode.Success;
}

export type CopilotResponseStatus =
  | FailedResponseStatus
  | PendingResponseStatus
  | SuccessResponseStatus;

export interface CopilotResponsePayload {
  data: {
    generateCopilotResponse: CopilotResponse;
  };
}

export interface CopilotResponse {
  threadId: string;
  runId?: string | null;
  status: CopilotResponseStatus;
  messages: CopilotMessageOutput[];
  extensions?: {
    openaiAssistantAPI?: {
      runId?: string | null;
      threadId?: string | null;
    } | null;
  } | null;
  metaEvents?: unknown[];
}

