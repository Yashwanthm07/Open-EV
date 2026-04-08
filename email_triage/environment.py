"""
Email Triage Environment — Core Logic

Implements the OpenEnv interface:
  reset() → EmailTriageObservation
  step(action) → (EmailTriageObservation, reward, done, info)
    state() → EmailTriageState
"""
from __future__ import annotations

import copy
import uuid
from typing import Optional, Tuple

from .data import TASKS
from .graders import compute_episode_score, grade_action
from .models import (
    EmailData,
    EmailTriageAction,
    EmailTriageObservation,
    EmailTriageReward,
    EmailTriageState,
)


class EmailTriageEnvironment:
    """
    OpenEnv-compatible Email Triage environment.

    Simulates a realistic inbox management task where the agent must process
    emails one by one, deciding how to handle each one (label, reply, forward,
    archive, delete, snooze, or flag).

    Tasks
    -----
    email_triage_easy   — 5 emails, clear spam/urgent signals
    email_triage_medium — 8 emails, mixed priorities, replies needed
    email_triage_hard   — 10 emails, complex, high-stakes decisions

    Reward shaping
    --------------
    Per-step reward: quality of each individual email action [0.0 – 1.0]
    Partial progress: incremental credit for reply quality, keyword coverage
    End-of-episode bonus: +0.2 if final score >= 0.8 (excellent performance)
    Penalty: -0.1 per invalid/unrecognised action_type
    Penalty: -0.05 per step that does nothing (no action fields provided)
    """

    SUPPORTS_CONCURRENT_SESSIONS = True

    VALID_ACTION_TYPES = {
        "label", "reply", "forward", "archive", "delete", "snooze", "flag"
    }
    VALID_LABELS = {"urgent", "normal", "spam", "needs_reply", "archive"}

    def __init__(self, task_name: str = "email_triage_easy"):
        if task_name not in TASKS:
            raise ValueError(
                f"Unknown task '{task_name}'. "
                f"Available: {list(TASKS.keys())}"
            )
        self._task_name = task_name
        self._task_config = TASKS[task_name]
        self._state = EmailTriageState()
        self._inbox: list[EmailData] = []
        self._correct_actions: dict = {}
        self._agent_actions: dict = {}
        self._current_idx: int = 0

    # ── OpenEnv interface ──────────────────────────────────────────────────

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs,
    ) -> EmailTriageObservation:
        """Reset the environment to a fresh inbox."""
        cfg = self._task_config
        self._inbox = copy.deepcopy(cfg["emails"])
        self._correct_actions = copy.deepcopy(cfg["correct_actions"])
        self._agent_actions = {}
        self._current_idx = 0

        self._state = EmailTriageState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            task_name=self._task_name,
            inbox=copy.deepcopy(self._inbox),
            correct_actions=copy.deepcopy(self._correct_actions),
            agent_actions={},
            current_email_idx=0,
            total_score=0.0,
            max_steps=cfg["max_steps"],
        )

        first_email = self._inbox[0] if self._inbox else None
        return EmailTriageObservation(
            done=False,
            reward=None,
            email=first_email,
            inbox_size=len(self._inbox),
            processed_count=0,
            last_action_result="Welcome! Triage the emails one by one. "
                               "Use action_type: label/reply/forward/archive/delete/snooze/flag",
            score_so_far=0.0,
            triaged_emails=[],
        )

    def step(
        self,
        action: EmailTriageAction,
        timeout_s: Optional[float] = None,
        **kwargs,
    ) -> Tuple[EmailTriageObservation, float, bool, dict]:
        """
        Process the agent's action on the current email.

        Returns (observation, reward, done, info)
        """
        self._state.step_count += 1

        # ── Guard: inbox already empty ──────────────────────────────────────
        if self._current_idx >= len(self._inbox):
            reward_model = EmailTriageReward(
                value=0.0,
                step_score=0.0,
                episode_bonus=0.0,
                penalty=0.0,
                final_score=self._state.total_score,
                explanation="Inbox is empty. Episode complete.",
            )
            obs = self._make_observation(
                reward=0.0,
                done=True,
                last_result="Inbox is empty. Episode complete.",
            )
            return obs, 0.0, True, {"reason": "inbox_empty", "reward": reward_model.model_dump()}

        current_email = self._inbox[self._current_idx]

        # ── Validate action ─────────────────────────────────────────────────
        action_type = (action.action_type or "").lower().strip()
        invalid_penalty = 0.0

        if action_type not in self.VALID_ACTION_TYPES:
            invalid_penalty = -0.1
            reward_model = EmailTriageReward(
                value=invalid_penalty,
                step_score=0.0,
                episode_bonus=0.0,
                penalty=abs(invalid_penalty),
                final_score=self._state.total_score,
                explanation="Invalid action type.",
            )
            result = (
                f"⚠ Invalid action_type '{action_type}'. "
                f"Valid types: {sorted(self.VALID_ACTION_TYPES)}. "
                f"Penalty: -0.1. Email not advanced."
            )
            obs = self._make_observation(
                reward=invalid_penalty,
                done=False,
                last_result=result,
            )
            return obs, invalid_penalty, False, {"error": "invalid_action_type", "reward": reward_model.model_dump()}

        # ── No-op detection ─────────────────────────────────────────────────
        is_noop = (
            action_type == "label" and not action.label
            and not action.reply_text
            and not action.forward_to
        )
        if is_noop:
            noop_penalty = -0.05
            reward_model = EmailTriageReward(
                value=noop_penalty,
                step_score=0.0,
                episode_bonus=0.0,
                penalty=abs(noop_penalty),
                final_score=self._state.total_score,
                explanation="No-op action.",
            )
            result = "⚠ No-op action detected (no fields provided). Penalty: -0.05."
            obs = self._make_observation(
                reward=noop_penalty,
                done=False,
                last_result=result,
            )
            return obs, noop_penalty, False, {"error": "noop", "reward": reward_model.model_dump()}

        # ── Store agent's action ────────────────────────────────────────────
        agent_action_record = {
            "action_type": action_type,
            "label": action.label,
            "reply_text": action.reply_text,
            "forward_to": action.forward_to,
            "reasoning": action.reasoning,
        }
        self._agent_actions[current_email.id] = agent_action_record

        # ── Grade the action ────────────────────────────────────────────────
        correct = self._correct_actions.get(current_email.id, {})
        step_score, feedback = grade_action(agent_action_record, correct)

        # ── Advance to next email ───────────────────────────────────────────
        self._current_idx += 1
        self._state.current_email_idx = self._current_idx
        self._state.agent_actions = copy.deepcopy(self._agent_actions)

        # ── Running score ───────────────────────────────────────────────────
        current_total = compute_episode_score(
            self._agent_actions, self._correct_actions
        )
        self._state.total_score = current_total

        # ── Check done ──────────────────────────────────────────────────────
        all_processed = self._current_idx >= len(self._inbox)
        step_limit = self._state.step_count >= self._state.max_steps
        done = all_processed or step_limit

        # ── End-of-episode bonus ────────────────────────────────────────────
        reward = step_score
        episode_bonus = 0.0
        if done and current_total >= 0.8:
            episode_bonus = 0.2
            reward += episode_bonus  # Bonus for excellent overall performance
            feedback += " 🎯 Excellent episode! +0.2 bonus."
        elif done and current_total >= 0.6:
            feedback += f" Episode complete. Final score: {current_total:.3f}"

        result = (
            f"Email '{current_email.subject[:50]}' processed. "
            f"Score: {step_score:.2f}. {feedback}"
        )

        obs = self._make_observation(
            reward=reward,
            done=done,
            last_result=result,
        )

        reward_model = EmailTriageReward(
            value=reward,
            step_score=step_score,
            episode_bonus=episode_bonus,
            penalty=0.0,
            final_score=current_total,
            explanation=feedback,
        )

        info = {
            "email_id": current_email.id,
            "step_score": step_score,
            "episode_score": current_total,
            "feedback": feedback,
            "done_reason": "all_processed" if all_processed else
                          "step_limit" if step_limit else "ongoing",
            "reward": reward_model.model_dump(),
        }

        return obs, reward, done, info

    def state(self) -> EmailTriageState:
        """Return current full state (not shown to agent during training)."""
        return self._state

    @property
    def current_state(self) -> EmailTriageState:
        """Backward-compatible accessor for callers that treated state as a property."""
        return self._state

    # ── Helpers ────────────────────────────────────────────────────────────

    def _make_observation(
        self,
        reward: float,
        done: bool,
        last_result: str,
    ) -> EmailTriageObservation:
        """Build an observation from current environment state."""
        next_email = (
            self._inbox[self._current_idx]
            if self._current_idx < len(self._inbox)
            else None
        )

        triaged = [
            {
                "email_id": eid,
                "action_type": act.get("action_type"),
                "label": act.get("label"),
            }
            for eid, act in self._agent_actions.items()
        ]

        return EmailTriageObservation(
            done=done,
            reward=reward,
            email=next_email,
            inbox_size=max(0, len(self._inbox) - self._current_idx),
            processed_count=self._current_idx,
            last_action_result=last_result,
            score_so_far=self._state.total_score,
            triaged_emails=triaged,
        )

    # ── Summary ────────────────────────────────────────────────────────────

    def get_episode_summary(self) -> dict:
        """Return end-of-episode performance summary."""
        final_score = compute_episode_score(
            self._agent_actions, self._correct_actions
        )
        per_email = {}
        for email_id, correct in self._correct_actions.items():
            agent = self._agent_actions.get(email_id)
            if agent:
                score, feedback = grade_action(agent, correct)
            else:
                score, feedback = 0.0, "Not processed"
            per_email[email_id] = {"score": score, "feedback": feedback}

        return {
            "task": self._task_name,
            "episode_id": self._state.episode_id,
            "steps_taken": self._state.step_count,
            "emails_processed": self._current_idx,
            "total_emails": len(self._inbox),
            "final_score": final_score,
            "per_email_scores": per_email,
        }
