"""
Agent graders for the Email Triage environment.

Each grader takes the agent's action and the expected correct action,
then returns a float score in [0.0, 1.0].

Grading is deterministic and reproducible.
"""
from __future__ import annotations

from typing import Optional


# ── Per-action scoring ────────────────────────────────────────────────────────

def grade_label_action(
    agent_label: Optional[str],
    expected_label: Optional[str],
) -> float:
    """Grade a labeling action. Full credit for exact match, 0 otherwise."""
    if not agent_label or not expected_label:
        return 0.0
    return 1.0 if agent_label.lower().strip() == expected_label.lower().strip() else 0.0


def grade_reply_action(
    agent_reply: Optional[str],
    expected_label: Optional[str],
    key_content: Optional[list] = None,
) -> float:
    """
    Grade a reply action.

    Scoring:
      - 0.4 for providing any non-trivial reply (≥20 chars)
      - 0.3 for urgency level awareness (reply to urgent emails vs normal)
      - 0.3 for key content coverage (partial credit per keyword hit)
    """
    if not agent_reply:
        return 0.0

    score = 0.0
    reply_lower = agent_reply.lower()
    reply_len = len(agent_reply.strip())

    # Basic reply quality (not just a one-liner)
    if reply_len >= 20:
        score += 0.4
    elif reply_len >= 5:
        score += 0.1

    # Urgency awareness
    if expected_label == "urgent":
        if reply_len >= 50:
            score += 0.3  # Urgent emails deserve substantive replies
        elif reply_len >= 20:
            score += 0.1
    elif reply_len >= 20:
        score += 0.2  # Non-urgent replies still need to be meaningful

    # Key content coverage
    if key_content:
        hits = sum(1 for kw in key_content if kw.lower() in reply_lower)
        content_score = min(hits / len(key_content), 1.0)
        score += 0.3 * content_score
    elif reply_len >= 20:
        score += 0.1

    return min(score, 1.0)


def grade_forward_action(
    agent_forward_to: Optional[str],
    expected_label: Optional[str],
    key_content: Optional[list] = None,
) -> float:
    """
    Grade a forward action.

    Scoring:
      - 0.5 for providing a forward destination
      - 0.3 for destination relevance (contains expected recipient keywords)
      - 0.2 urgency awareness
    """
    if not agent_forward_to:
        return 0.0

    score = 0.5  # Credit for forwarding at all

    forward_lower = agent_forward_to.lower()

    # Check if forward destination looks plausible
    if key_content:
        hits = sum(1 for kw in key_content if kw.lower() in forward_lower)
        score += 0.3 * min(hits / len(key_content), 1.0)
    else:
        # Generic: any non-trivial forward target
        if "@" in agent_forward_to or len(agent_forward_to) > 4:
            score += 0.3

    # Urgency bonus
    if expected_label == "urgent":
        score += 0.2
    else:
        score += 0.2

    return min(score, 1.0)


def grade_archive_action(expected_action_type: str) -> float:
    """
    Archiving is correct when expected, penalized when not.
    """
    if expected_action_type == "archive":
        return 1.0
    # Archiving something that needed action is partial credit only
    if expected_action_type in ("label",):
        return 0.2  # Not completely wrong, but missed the point
    return 0.0


def grade_delete_action(expected_action_type: str, expected_label: Optional[str]) -> float:
    """Deleting is acceptable for spam, bad for everything else."""
    if expected_label == "spam":
        return 1.0  # Deleting spam is fine
    if expected_action_type == "archive":
        return 0.3  # Over-aggressive but not terrible
    return 0.0


def grade_flag_action(expected_label: Optional[str]) -> float:
    """Flagging as attention-needed — partial credit for urgent items."""
    if expected_label == "urgent":
        return 0.6  # Good awareness, but didn't take full action
    if expected_label == "needs_reply":
        return 0.4  # Acceptable
    return 0.1


def grade_snooze_action(expected_action_type: str, expected_label: Optional[str]) -> float:
    """Snoozing — acceptable for lower priority items, bad for urgent."""
    if expected_label == "urgent":
        return 0.0  # Never snooze urgent
    if expected_action_type in ("archive", "label") and expected_label == "normal":
        return 0.5  # Reasonable but not ideal
    return 0.2


# ── Main grading function ─────────────────────────────────────────────────────

def grade_action(
    agent_action: dict,
    correct_action: dict,
) -> tuple[float, str]:
    """
    Grade an agent's action against the correct action.

    Parameters
    ----------
    agent_action : dict
        Keys: action_type, label, reply_text, forward_to, reasoning
    correct_action : dict
        Keys: action_type, label, key_content (optional), explanation

    Returns
    -------
    score : float in [0.0, 1.0]
    feedback : str explaining the score
    """
    agent_type = (agent_action.get("action_type") or "").lower().strip()
    expected_type = (correct_action.get("action_type") or "").lower().strip()
    expected_label = correct_action.get("label")
    key_content = correct_action.get("key_content")
    explanation = correct_action.get("explanation", "")

    # ── Action type matches ──────────────────────────────────────────────────
    if agent_type == expected_type:
        if expected_type == "label":
            score = grade_label_action(agent_action.get("label"), expected_label)
            if score == 1.0:
                feedback = f"✓ Correct label '{expected_label}'. {explanation}"
            else:
                agent_lbl = agent_action.get("label", "none")
                feedback = f"✗ Wrong label '{agent_lbl}' (expected '{expected_label}'). {explanation}"

        elif expected_type == "reply":
            score = grade_reply_action(
                agent_action.get("reply_text"),
                expected_label,
                key_content,
            )
            quality = "good" if score >= 0.7 else "partial" if score >= 0.4 else "poor"
            feedback = f"{'✓' if score >= 0.7 else '~'} Reply quality: {quality} ({score:.2f}). {explanation}"

        elif expected_type == "forward":
            score = grade_forward_action(
                agent_action.get("forward_to"),
                expected_label,
                key_content,
            )
            feedback = f"{'✓' if score >= 0.7 else '~'} Forward score: {score:.2f}. {explanation}"

        elif expected_type == "archive":
            score = grade_archive_action(expected_type)
            feedback = f"✓ Correctly archived. {explanation}"

        elif expected_type == "delete":
            score = grade_delete_action(expected_type, expected_label)
            feedback = f"✓ Deleted. Score: {score:.2f}. {explanation}"

        else:
            score = 0.5
            feedback = f"~ Action type matched but unrecognized type '{expected_type}'"

    # ── Action type mismatch — partial credit possible ───────────────────────
    else:
        score, feedback = _grade_mismatched_action(
            agent_type, expected_type, expected_label, agent_action, correct_action
        )

    return round(score, 3), feedback


def _grade_mismatched_action(
    agent_type: str,
    expected_type: str,
    expected_label: Optional[str],
    agent_action: dict,
    correct_action: dict,
) -> tuple[float, str]:
    """Handle partial credit for mismatched action types."""
    explanation = correct_action.get("explanation", "")

    # Archiving instead of labeling — some overlap
    if agent_type == "archive" and expected_type == "label":
        if expected_label in ("normal", "archive"):
            return 0.5, f"~ Archived instead of labeled '{expected_label}'. Acceptable. {explanation}"
        return 0.1, f"✗ Archived instead of '{expected_type}' (label: {expected_label}). {explanation}"

    # Flagging instead of labeling urgent — good awareness
    if agent_type == "flag" and expected_label == "urgent":
        return 0.4, f"~ Flagged (expected label urgent). Partial credit. {explanation}"

    # Labeling spam as delete
    if agent_type == "delete" and expected_label == "spam":
        return 0.8, f"~ Deleted spam (expected label='spam'). Reasonable. {explanation}"

    # Replying to something that just needed a label
    if agent_type == "reply" and expected_type == "label":
        if expected_label in ("urgent", "needs_reply"):
            return 0.4, f"~ Replied to email that needed label '{expected_label}'. Partial credit. {explanation}"
        return 0.1, f"✗ Replied unnecessarily (expected label='{expected_label}'). {explanation}"

    # Forwarding when reply was expected — sometimes okay
    if agent_type == "forward" and expected_type == "reply":
        return 0.3, f"~ Forwarded instead of replying. {explanation}"

    # Generic mismatch
    return 0.0, f"✗ Wrong action '{agent_type}' (expected '{expected_type}'). {explanation}"


# ── Episode-level scoring ─────────────────────────────────────────────────────

def compute_episode_score(agent_actions: dict, correct_actions: dict) -> float:
    """
    Compute overall episode score.

    Returns mean of per-email scores, weighted by urgency:
    - urgent/security emails: weight 2.0
    - needs_reply: weight 1.5
    - normal/archive/spam: weight 1.0
    """
    if not correct_actions:
        return 0.0

    total_weight = 0.0
    weighted_score = 0.0

    for email_id, correct in correct_actions.items():
        agent = agent_actions.get(email_id)
        if agent is None:
            # Email not processed — zero score
            per_score = 0.0
        else:
            per_score, _ = grade_action(agent, correct)

        label = correct.get("label", "normal")
        weight = 2.0 if label == "urgent" else 1.5 if label == "needs_reply" else 1.0

        weighted_score += per_score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(weighted_score / total_weight, 4)
