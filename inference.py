"""
Email Triage OpenEnv — Inference Script

Runs an LLM agent against all 3 email triage tasks and emits structured
stdout logs in the mandatory [START] / [STEP] / [END] format.

Environment variables
---------------------
API_BASE_URL   LLM endpoint (default: https://router.huggingface.co/v1)
MODEL_NAME     Model identifier (default: Qwen/Qwen2.5-72B-Instruct)
HF_TOKEN       HuggingFace / API key
TASK_NAME      Run a single task (default: run all 3)

Usage
-----
    python inference.py                           # run all 3 tasks
    TASK_NAME=email_triage_easy python inference.py  # run single task

Stdout format (mandatory)
-------------------------
[START] task=<task_name> env=email_triage model=<model_name>
[STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...>
"""

import json
import os
import sys
import textwrap
from typing import List, Optional

from openai import OpenAI

# ── Configuration ─────────────────────────────────────────────────────────────

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or "dummy_key"
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK = "email_triage"
MAX_STEPS = 15
TEMPERATURE = 0.2
MAX_TOKENS = 512
SUCCESS_SCORE_THRESHOLD = 0.5

TASKS_TO_RUN = (
    [os.getenv("TASK_NAME")]
    if os.getenv("TASK_NAME")
    else ["email_triage_easy", "email_triage_medium", "email_triage_hard"]
)

# ── Logging helpers ───────────────────────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int, action: str, reward: float, done: bool, error: Optional[str]
) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    # Sanitise action string (no newlines allowed in log line)
    action_clean = action.replace("\n", " ").replace("\r", "")[:120]
    print(
        f"[STEP] step={step} action={action_clean} "
        f"reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(
    success: bool, steps: int, score: float, rewards: List[float]
) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent("""
You are an expert executive assistant tasked with triaging a corporate email inbox.

For each email you receive, you must decide how to handle it by providing a JSON action.

AVAILABLE ACTIONS:
  label     — Classify the email with a label
  reply     — Draft a reply to the email
  forward   — Forward the email to someone else
  archive   — Archive the email (no action needed)
  delete    — Delete the email (spam/irrelevant)
  snooze    — Snooze the email for later
  flag      — Flag the email for follow-up

VALID LABELS: urgent, normal, spam, needs_reply, archive

PRIORITIZATION RULES:
1. Security incidents, production outages → label:urgent (immediate)
2. Executive requests with deadlines → label:urgent + reply
3. Customer complaints from long-term customers → reply with empathy
4. Invoices/billing → forward to accounts payable
5. Legal documents → forward to legal team
6. Newsletters/automated notifications → archive
7. Obvious spam/phishing → label:spam or delete

RESPONSE FORMAT — You must respond with ONLY a valid JSON object:
{
  "action_type": "label",
  "label": "urgent",
  "reply_text": null,
  "forward_to": null,
  "reasoning": "Brief explanation"
}

For reply actions, set "reply_text" to a professional response.
For forward actions, set "forward_to" to the appropriate recipient.
Do not include any text outside the JSON.
""").strip()


# ── Prompt building ───────────────────────────────────────────────────────────

def build_prompt(observation: dict, step: int, history: List[str]) -> str:
    """Build user prompt from the current observation."""
    email = observation.get("email")
    if not email:
        return "The inbox is empty. No email to process."

    history_block = "\n".join(history[-3:]) if history else "None"

    email_block = (
        f"FROM: {email.get('sender')} <{email.get('sender_email')}>\n"
        f"SUBJECT: {email.get('subject')}\n"
        f"DATE: {email.get('timestamp', 'unknown')}\n"
        f"THREAD: {email.get('thread_length', 1)} messages | "
        f"ATTACHMENT: {email.get('has_attachment', False)}\n"
        f"\n{email.get('body', '')}"
    )

    return textwrap.dedent(f"""
Step {step} | Emails remaining: {observation.get('inbox_size', 0)} | Score so far: {observation.get('score_so_far', 0):.2f}

--- EMAIL TO TRIAGE ---
{email_block}
--- END EMAIL ---

Last result: {observation.get('last_action_result', '')}

Recent history:
{history_block}

Provide your JSON action for this email.
""").strip()


# ── LLM call ──────────────────────────────────────────────────────────────────

def get_model_action(
    client: OpenAI,
    observation: dict,
    step: int,
    history: List[str],
) -> tuple[dict, str]:
    """
    Call the LLM and parse its JSON action.

    Returns (action_dict, raw_response_string)
    """
    prompt = build_prompt(observation, step, history)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        raw = (completion.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"[DEBUG] Model call failed: {exc}", flush=True)
        raw = '{"action_type": "archive", "reasoning": "fallback"}'

    # Parse JSON — strip markdown fences if present
    clean = raw.replace("```json", "").replace("```", "").strip()
    try:
        action = json.loads(clean)
    except json.JSONDecodeError:
        print(f"[DEBUG] JSON parse failed on: {raw[:200]}", flush=True)
        action = {"action_type": "archive", "reasoning": "parse_error"}

    return action, raw


# ── Episode runner ────────────────────────────────────────────────────────────

def run_episode(
    client: OpenAI,
    task_name: str,
    base_url: str,
) -> tuple[bool, int, float, List[float]]:
    """
    Run a full episode for a task against the local environment server.

    Returns (success, steps_taken, final_score, rewards_list)
    """
    import urllib.request

    server_base = base_url.rstrip("/")

    def post_json(endpoint: str, payload: dict) -> dict:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{server_base}{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    # Reset
    reset_resp = post_json("/reset", {"task_name": task_name, "session_id": task_name})
    observation = reset_resp.get("observation", {})

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    done = False
    score = 0.0

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    for step in range(1, MAX_STEPS + 1):
        if done or not observation.get("email"):
            break

        action_dict, raw = get_model_action(client, observation, step, history)

        # Build step request
        step_payload = {
            "session_id": task_name,
            "action_type": action_dict.get("action_type", "archive"),
            "label": action_dict.get("label"),
            "reply_text": action_dict.get("reply_text"),
            "forward_to": action_dict.get("forward_to"),
            "reasoning": action_dict.get("reasoning"),
        }

        error_msg = None
        try:
            step_resp = post_json("/step", step_payload)
            reward = float(step_resp.get("reward", 0.0))
            done = bool(step_resp.get("done", False))
            observation = step_resp.get("observation", {})
            info = step_resp.get("info", {})
            error_msg = info.get("error") if info.get("error") else None
        except Exception as exc:
            reward = 0.0
            error_msg = str(exc)[:80]
            print(f"[DEBUG] Step {step} HTTP error: {exc}", flush=True)

        rewards.append(reward)
        steps_taken = step

        action_str = (
            f"{action_dict.get('action_type', '?')}("
            f"label={action_dict.get('label', 'null')})"
        )

        log_step(
            step=step,
            action=action_str,
            reward=reward,
            done=done,
            error=error_msg,
        )

        history.append(
            f"Step {step}: {action_str} → reward {reward:+.2f} | "
            f"{observation.get('last_action_result', '')[:80]}"
        )

    # Fetch final score from summary endpoint
    try:
        req = urllib.request.Request(
            f"{server_base}/summary?session_id={task_name}", method="GET"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            summary = json.loads(resp.read())
        score = float(summary.get("final_score", 0.0))
    except Exception:
        score = (
            sum(rewards) / len(rewards) if rewards else 0.0
        )

    score = min(max(score, 0.0), 1.0)
    success = score >= SUCCESS_SCORE_THRESHOLD
    return success, steps_taken, score, rewards


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # Server base URL — local if running alongside the server, else from env
    server_url = os.getenv("ENV_BASE_URL", "http://localhost:7860")

    all_successes = []

    for task_name in TASKS_TO_RUN:
        rewards: List[float] = []
        steps_taken = 0
        success = False
        score = 0.0

        try:
            success, steps_taken, score, rewards = run_episode(
                client, task_name, server_url
            )
        except Exception as exc:
            print(f"[DEBUG] Episode failed for {task_name}: {exc}", flush=True)
            log_end(success=False, steps=0, score=0.0, rewards=[])
        else:
            log_end(
                success=success,
                steps=steps_taken,
                score=score,
                rewards=rewards,
            )

        all_successes.append(success)

    # Summary across all tasks
    overall = sum(all_successes) / len(all_successes) if all_successes else 0.0
    print(
        f"[SUMMARY] tasks={len(TASKS_TO_RUN)} success_rate={overall:.2f} "
        f"passed={sum(all_successes)}/{len(all_successes)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
