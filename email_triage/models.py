"""
Email Triage Environment — Typed Models

Pydantic models used by the OpenEnv-compatible environment and API server.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Base types ────────────────────────────────────────────────────────────────

class OpenEnvModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Action(OpenEnvModel):
    """Base action type."""


class Observation(OpenEnvModel):
    """Base observation type."""
    done: bool = False
    reward: Optional[float] = None


class Reward(OpenEnvModel):
    """Base reward model."""
    value: float = 0.0
    step_score: float = 0.0
    episode_bonus: float = 0.0
    penalty: float = 0.0
    final_score: Optional[float] = None
    explanation: str = ""


class State(OpenEnvModel):
    """Base state type."""
    episode_id: Optional[str] = None
    step_count: int = 0


# ── Domain constants ──────────────────────────────────────────────────────────

VALID_ACTION_TYPES = {"label", "reply", "forward", "archive", "delete", "snooze", "flag"}
VALID_LABELS = {"urgent", "normal", "spam", "needs_reply", "archive"}


# ── Email Triage Models ───────────────────────────────────────────────────────

class EmailTriageAction(Action):
    """
    An action the agent takes on the current email.

    Fields
    ------
    action_type : str
        One of: label, reply, forward, archive, delete, snooze, flag
    label : str | None
        Required when action_type == 'label'.
        One of: urgent, normal, spam, needs_reply, archive
    reply_text : str | None
        Draft reply text (for action_type == 'reply').
    forward_to : str | None
        Recipient email/name (for action_type == 'forward').
    reasoning : str | None
        Agent's explanation for the action (used in grading).
    """
    action_type: str = Field(default="")
    label: Optional[str] = None
    reply_text: Optional[str] = None
    forward_to: Optional[str] = None
    reasoning: Optional[str] = None


class EmailData(OpenEnvModel):
    """Represents a single email in the inbox."""
    id: str = ""
    subject: str = ""
    sender: str = ""
    sender_email: str = ""
    body: str = ""
    timestamp: str = ""
    thread_length: int = 1
    has_attachment: bool = False
    is_reply: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmailTriageObservation(Observation):
    """
    What the agent sees after each step.

    Fields
    ------
    email : EmailData | None
        Current email to triage (None when inbox is empty).
    inbox_size : int
        Number of emails remaining to process.
    processed_count : int
        How many emails have been processed this episode.
    last_action_result : str
        Feedback on the most recent action taken.
    score_so_far : float
        Running accuracy score [0.0 – 1.0].
    triaged_emails : list[dict]
        History of processed email IDs and actions.
    """
    email: Optional[EmailData] = None
    inbox_size: int = 0
    processed_count: int = 0
    last_action_result: str = ""
    score_so_far: float = 0.0
    triaged_emails: List[dict] = Field(default_factory=list)


class EmailTriageState(State):
    """Full internal state (not shown to agent during training)."""
    task_name: str = ""
    inbox: List[EmailData] = Field(default_factory=list)
    correct_actions: Dict[str, Any] = Field(default_factory=dict)
    agent_actions: Dict[str, Any] = Field(default_factory=dict)
    current_email_idx: int = 0
    total_score: float = 0.0
    max_steps: int = 20


class EmailTriageReward(Reward):
    """Structured reward payload for dense feedback and grading."""
    pass
