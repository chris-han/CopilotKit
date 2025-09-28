"""Dataclass representations of CopilotKit runtime GraphQL types."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from dataclasses import is_dataclass
from enum import Enum
from typing import Any, List, Optional, Union


class MessageStatusCode(str, Enum):
    FAILED = "Failed"
    PENDING = "Pending"
    SUCCESS = "Success"


@dataclass
class FailedMessageStatus:
    typename: str = field(init=False, default="FailedMessageStatus", metadata={"alias": "__typename"})
    code: MessageStatusCode = MessageStatusCode.FAILED
    reason: str = ""


@dataclass
class PendingMessageStatus:
    typename: str = field(init=False, default="PendingMessageStatus", metadata={"alias": "__typename"})
    code: MessageStatusCode = MessageStatusCode.PENDING


@dataclass
class SuccessMessageStatus:
    typename: str = field(init=False, default="SuccessMessageStatus", metadata={"alias": "__typename"})
    code: MessageStatusCode = MessageStatusCode.SUCCESS


MessageStatus = Union[FailedMessageStatus, PendingMessageStatus, SuccessMessageStatus]


class MessageRole(str, Enum):
    ASSISTANT = "assistant"
    DEVELOPER = "developer"
    SYSTEM = "system"
    TOOL = "tool"
    USER = "user"


@dataclass
class BaseMessageOutput:
    id: str
    createdAt: str
    status: MessageStatus


@dataclass
class TextMessageOutput(BaseMessageOutput):
    typename: str = field(init=False, default="TextMessageOutput", metadata={"alias": "__typename"})
    content: List[str] = field(default_factory=list)
    role: MessageRole = MessageRole.ASSISTANT
    parentMessageId: Optional[str] = None


CopilotMessageOutput = TextMessageOutput


class ResponseStatusCode(str, Enum):
    FAILED = "Failed"
    PENDING = "Pending"
    SUCCESS = "Success"


@dataclass
class FailedResponseStatus:
    typename: str = field(init=False, default="FailedResponseStatus", metadata={"alias": "__typename"})
    code: ResponseStatusCode = ResponseStatusCode.FAILED
    reason: str = ""
    details: Optional[Any] = None


@dataclass
class PendingResponseStatus:
    typename: str = field(init=False, default="PendingResponseStatus", metadata={"alias": "__typename"})
    code: ResponseStatusCode = ResponseStatusCode.PENDING


@dataclass
class SuccessResponseStatus:
    typename: str = field(init=False, default="SuccessResponseStatus", metadata={"alias": "__typename"})
    code: ResponseStatusCode = ResponseStatusCode.SUCCESS


CopilotResponseStatus = Union[
    FailedResponseStatus,
    PendingResponseStatus,
    SuccessResponseStatus,
]


@dataclass
class CopilotResponse:
    typename: str = field(init=False, default="CopilotResponse", metadata={"alias": "__typename"})
    threadId: str
    runId: Optional[str]
    status: CopilotResponseStatus
    messages: List[CopilotMessageOutput]
    extensions: Optional[Any] = None
    metaEvents: List[Any] = field(default_factory=list)


@dataclass
class CopilotResponsePayload:
    data: dict


def to_serializable(value: Any) -> Any:
    """Recursively convert dataclass/enum structures to JSON-serialisable data."""

    if is_dataclass(value):
        result = {}
        for field_info in fields(value):
            key = field_info.metadata.get("alias", field_info.name)
            result[key] = to_serializable(getattr(value, field_info.name))
        return result
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_serializable(val) for key, val in value.items()}
    return value
