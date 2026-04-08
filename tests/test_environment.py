"""
Tests for the Email Triage OpenEnv environment.

Run with: pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from email_triage.environment import EmailTriageEnvironment
from email_triage.graders import (
    compute_episode_score,
    grade_action,
    grade_archive_action,
    grade_delete_action,
    grade_label_action,
    grade_reply_action,
)
from email_triage.models import EmailTriageAction


# ── Grader unit tests ─────────────────────────────────────────────────────────

class TestLabelGrader:
    def test_exact_match(self):
        assert grade_label_action("urgent", "urgent") == 1.0

    def test_case_insensitive(self):
        assert grade_label_action("URGENT", "urgent") == 1.0

    def test_wrong_label(self):
        assert grade_label_action("spam", "urgent") == 0.0

    def test_none_label(self):
        assert grade_label_action(None, "urgent") == 0.0

    def test_all_valid_labels(self):
        for lbl in ("urgent", "normal", "spam", "needs_reply", "archive"):
            assert grade_label_action(lbl, lbl) == 1.0


class TestReplyGrader:
    def test_good_reply(self):
        score = grade_reply_action(
            "I sincerely apologize for the delay on your order. "
            "I will investigate and arrange a refund immediately.",
            "urgent",
            ["apologize", "investigate", "refund"],
        )
        assert score >= 0.7

    def test_empty_reply(self):
        assert grade_reply_action(None, "urgent", None) == 0.0

    def test_minimal_reply(self):
        score = grade_reply_action("ok", "normal", None)
        assert score < 0.5

    def test_partial_keyword_coverage(self):
        score_full = grade_reply_action(
            "I apologize and will investigate and arrange a refund",
            "urgent",
            ["apologize", "investigate", "refund"],
        )
        score_partial = grade_reply_action(
            "I apologize for the issue",
            "urgent",
            ["apologize", "investigate", "refund"],
        )
        assert score_full > score_partial


class TestArchiveGrader:
    def test_correct_archive(self):
        assert grade_archive_action("archive") == 1.0

    def test_wrong_archive(self):
        assert grade_archive_action("reply") == 0.0


class TestDeleteGrader:
    def test_delete_spam(self):
        assert grade_delete_action("label", "spam") == 1.0

    def test_delete_urgent(self):
        assert grade_delete_action("label", "urgent") == 0.0


class TestGradeAction:
    def test_correct_label_action(self):
        score, feedback = grade_action(
            {"action_type": "label", "label": "urgent"},
            {"action_type": "label", "label": "urgent"},
        )
        assert score == 1.0
        assert "✓" in feedback

    def test_wrong_label_action(self):
        score, feedback = grade_action(
            {"action_type": "label", "label": "spam"},
            {"action_type": "label", "label": "urgent"},
        )
        assert score == 0.0

    def test_reply_action(self):
        score, feedback = grade_action(
            {
                "action_type": "reply",
                "reply_text": "I apologize for the delay. I will investigate your order and arrange a refund.",
            },
            {
                "action_type": "reply",
                "label": "urgent",
                "key_content": ["apologize", "investigate", "refund"],
            },
        )
        assert score >= 0.7

    def test_delete_spam(self):
        score, _ = grade_action(
            {"action_type": "delete"},
            {"action_type": "label", "label": "spam"},
        )
        assert score == 0.8

    def test_archive_newsletter(self):
        score, _ = grade_action(
            {"action_type": "archive"},
            {"action_type": "archive", "label": "normal"},
        )
        assert score == 1.0

    def test_score_always_in_range(self):
        """All scores must be in [0.0, 1.0]."""
        test_cases = [
            ({"action_type": "label", "label": "urgent"}, {"action_type": "label", "label": "urgent"}),
            ({"action_type": "reply", "reply_text": "x" * 100}, {"action_type": "reply", "label": "urgent"}),
            ({"action_type": "delete"}, {"action_type": "label", "label": "spam"}),
            ({"action_type": "forward", "forward_to": "legal@company.com"}, {"action_type": "forward", "label": "urgent"}),
            ({"action_type": "archive"}, {"action_type": "archive", "label": "normal"}),
            ({"action_type": "snooze"}, {"action_type": "archive", "label": "normal"}),
            ({"action_type": "flag"}, {"action_type": "label", "label": "urgent"}),
        ]
        for agent, correct in test_cases:
            score, _ = grade_action(agent, correct)
            assert 0.0 <= score <= 1.0, f"Score {score} out of range for {agent} vs {correct}"


# ── Environment integration tests ─────────────────────────────────────────────

class TestEmailTriageEnvironment:
    def test_init_easy(self):
        env = EmailTriageEnvironment("email_triage_easy")
        assert env is not None

    def test_init_medium(self):
        env = EmailTriageEnvironment("email_triage_medium")
        assert env is not None

    def test_init_hard(self):
        env = EmailTriageEnvironment("email_triage_hard")
        assert env is not None

    def test_invalid_task(self):
        with pytest.raises(ValueError):
            EmailTriageEnvironment("nonexistent_task")

    def test_reset_returns_observation(self):
        env = EmailTriageEnvironment("email_triage_easy")
        obs = env.reset()
        assert obs.done is False
        assert obs.reward is None
        assert obs.email is not None
        assert obs.inbox_size == 5
        assert obs.processed_count == 0

    def test_reset_provides_first_email(self):
        env = EmailTriageEnvironment("email_triage_easy")
        obs = env.reset()
        assert obs.email.id == "easy_001"
        assert "Production server" in obs.email.subject

    def test_step_advances_inbox(self):
        env = EmailTriageEnvironment("email_triage_easy")
        env.reset()
        action = EmailTriageAction(action_type="label", label="urgent")
        obs, reward, done, info = env.step(action)
        assert obs.processed_count == 1
        assert obs.inbox_size == 4

    def test_step_reward_in_range(self):
        env = EmailTriageEnvironment("email_triage_easy")
        env.reset()
        action = EmailTriageAction(action_type="label", label="urgent")
        _, reward, _, _ = env.step(action)
        assert -0.2 <= reward <= 1.3

    def test_correct_actions_get_high_reward(self):
        env = EmailTriageEnvironment("email_triage_easy")
        env.reset()
        # easy_001: URGENT production alert
        action = EmailTriageAction(action_type="label", label="urgent")
        _, reward, _, _ = env.step(action)
        assert reward >= 0.9

    def test_wrong_actions_get_low_reward(self):
        env = EmailTriageEnvironment("email_triage_easy")
        env.reset()
        # easy_001 is urgent, labeling as spam is wrong
        action = EmailTriageAction(action_type="label", label="spam")
        _, reward, _, _ = env.step(action)
        assert reward < 0.5

    def test_spam_detection(self):
        env = EmailTriageEnvironment("email_triage_easy")
        obs = env.reset()
        # easy_001 is urgent — skip it
        env.step(EmailTriageAction(action_type="label", label="urgent"))
        # easy_002 is the prize scam
        action = EmailTriageAction(action_type="label", label="spam")
        _, reward, _, _ = env.step(action)
        assert reward >= 0.9

    def test_invalid_action_type_penalty(self):
        env = EmailTriageEnvironment("email_triage_easy")
        env.reset()
        action = EmailTriageAction(action_type="fly_to_moon", label="urgent")
        obs, reward, done, info = env.step(action)
        assert reward < 0.0
        assert "error" in info
        assert obs.processed_count == 0  # email not advanced

    def test_complete_easy_episode(self):
        """Perfect agent on easy task should score high."""
        env = EmailTriageEnvironment("email_triage_easy")
        env.reset()
        correct_sequence = [
            EmailTriageAction(action_type="label", label="urgent"),   # easy_001
            EmailTriageAction(action_type="label", label="spam"),     # easy_002
            EmailTriageAction(action_type="label", label="needs_reply"),  # easy_003
            EmailTriageAction(action_type="label", label="spam"),     # easy_004
            EmailTriageAction(action_type="label", label="urgent"),   # easy_005
        ]
        rewards = []
        for action in correct_sequence:
            _, reward, done, _ = env.step(action)
            rewards.append(reward)
        summary = env.get_episode_summary()
        assert summary["final_score"] >= 0.85

    def test_episode_ends_after_all_emails(self):
        env = EmailTriageEnvironment("email_triage_easy")
        env.reset()
        done = False
        steps = 0
        while not done and steps < 20:
            _, _, done, _ = env.step(EmailTriageAction(action_type="archive"))
            steps += 1
        assert done

    def test_state_returns_state_object(self):
        env = EmailTriageEnvironment("email_triage_easy")
        env.reset()
        state = env.state()
        assert state.task_name == "email_triage_easy"
        assert state.step_count == 0

    def test_state_updates_after_step(self):
        env = EmailTriageEnvironment("email_triage_easy")
        env.reset()
        env.step(EmailTriageAction(action_type="label", label="urgent"))
        assert env.state().step_count == 1

    def test_get_episode_summary(self):
        env = EmailTriageEnvironment("email_triage_easy")
        env.reset()
        env.step(EmailTriageAction(action_type="label", label="urgent"))
        summary = env.get_episode_summary()
        assert "final_score" in summary
        assert "per_email_scores" in summary
        assert 0.0 <= summary["final_score"] <= 1.0

    def test_reset_clears_previous_state(self):
        env = EmailTriageEnvironment("email_triage_easy")
        env.reset()
        env.step(EmailTriageAction(action_type="label", label="urgent"))
        env.step(EmailTriageAction(action_type="label", label="spam"))
        # Reset should clear everything
        obs = env.reset()
        assert obs.processed_count == 0
        assert obs.inbox_size == 5
        assert env.state().step_count == 0


# ── Reward shaping tests ───────────────────────────────────────────────────────

class TestRewardShaping:
    def test_partial_reply_credit(self):
        """Reply without key content should still get partial credit."""
        score, _ = grade_action(
            {"action_type": "reply", "reply_text": "Thank you for reaching out. I'll look into this."},
            {"action_type": "reply", "label": "urgent", "key_content": ["apologize", "investigate", "refund"]},
        )
        assert 0.3 < score < 0.8

    def test_flag_urgent_partial_credit(self):
        score, _ = grade_action(
            {"action_type": "flag"},
            {"action_type": "label", "label": "urgent"},
        )
        assert 0.3 <= score <= 0.6

    def test_episode_score_weighted_by_urgency(self):
        """Urgent emails should contribute more to episode score."""
        agent = {
            "e1": {"action_type": "label", "label": "urgent"},   # correct, urgent weight=2
            "e2": {"action_type": "label", "label": "normal"},   # correct, normal weight=1
        }
        correct = {
            "e1": {"action_type": "label", "label": "urgent"},
            "e2": {"action_type": "label", "label": "normal"},
        }
        score_both_correct = compute_episode_score(agent, correct)
        assert score_both_correct == pytest.approx(1.0, abs=0.01)

        agent_wrong_urgent = {
            "e1": {"action_type": "label", "label": "spam"},    # wrong, weight=2
            "e2": {"action_type": "label", "label": "normal"},  # correct, weight=1
        }
        score_wrong_urgent = compute_episode_score(agent_wrong_urgent, correct)
        assert score_wrong_urgent < 0.4  # penalty heavier due to urgent weight


# ── Determinism tests ─────────────────────────────────────────────────────────

class TestDeterminism:
    def test_same_action_same_score(self):
        """Grading must be deterministic."""
        for _ in range(5):
            score, _ = grade_action(
                {"action_type": "label", "label": "urgent"},
                {"action_type": "label", "label": "urgent"},
            )
            assert score == 1.0

    def test_reset_same_inbox_order(self):
        """Same task always starts with same email order."""
        env = EmailTriageEnvironment("email_triage_easy")
        obs1 = env.reset()
        email1_id = obs1.email.id
        obs2 = env.reset()
        email2_id = obs2.email.id
        assert email1_id == email2_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
