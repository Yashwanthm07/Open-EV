# 📧 Email Triage OpenEnv

> A real-world corporate email management environment for AI agent training and evaluation, built to the [OpenEnv](https://github.com/raun/openenv-course) specification.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compatible-blue)](https://github.com/raun/openenv-course)
[![HuggingFace](https://img.shields.io/badge/🤗-HuggingFace%20Space-yellow)](https://huggingface.co/spaces)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Why Email Triage?

Knowledge workers spend an estimated **2.5+ hours per day** on email. A capable AI agent that can triage an inbox — identifying what's urgent, what needs a reply, what's spam, and what can be archived — has immediate, real-world value.

This environment models the full complexity of that task:
- **Spam vs. legitimate** (easy signal)
- **Urgency detection** across ambiguous context
- **Drafting contextually appropriate replies**
- **Routing** (forward to legal, finance, security teams)
- **Competing priorities** when multiple items are time-sensitive

Unlike toy environments, the hard task includes genuinely difficult scenarios that even strong frontier models make mistakes on: whistleblower reports, retention-risk employees with competing offers, simultaneous P0 incidents, and media crisis management.

---

## Environment Structure

```
email-triage-env/
├── email_triage/
│   ├── __init__.py
│   ├── models.py          ← Typed Pydantic models (Action, Observation, Reward, State)
│   ├── environment.py     ← Core logic: reset() / step() / state
│   ├── graders.py         ← Deterministic per-action and episode scoring
│   └── data.py            ← 23 realistic synthetic emails + expected actions
├── server/
│   ├── __init__.py
│   └── app.py             ← FastAPI server (REST + WebSocket)
├── tests/
│   └── test_environment.py  ← 30+ unit and integration tests
├── inference.py           ← Baseline inference script (OpenAI client)
├── openenv.yaml           ← OpenEnv manifest
├── Dockerfile             ← HuggingFace Spaces compatible
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Tasks

### Task 1: `email_triage_easy` — Easy
**5 emails** with clear, unambiguous signals.

| Email | Correct Action | Why |
|-------|---------------|-----|
| Production server DOWN alert | `label: urgent` | Critical system outage |
| "You've WON $1,000!!!" | `label: spam` | Classic phishing scam |
| Team lunch RSVP request | `label: needs_reply` | Colleague needs response |
| Nigerian prince email | `label: spam` | Advance-fee fraud |
| AWS bill 3x normal spend | `label: urgent` | Billing anomaly |

Expected score — random agent: ~0.15 | GPT-4: ~0.90

---

### Task 2: `email_triage_medium` — Medium
**8 emails** with mixed priorities. Some require replies or forwarding.

| Email | Correct Action |
|-------|---------------|
| CFO needs Q4 numbers for board meeting in 3h | `reply: urgent` |
| ProductivityHub newsletter | `archive` |
| Long-term customer: order never arrived | `reply: urgent` |
| IT security: mandatory password reset by Jan 20 | `label: needs_reply` |
| Invoice from Acme Software ($3,600) | `forward` to accounts |
| HR: interview feedback needed by 3pm today | `reply: urgent` |
| LinkedIn work anniversary notification | `archive` |
| NDA needs legal review, $500K deal | `forward` to legal |

Expected score — random agent: ~0.12 | GPT-4: ~0.75

---

### Task 3: `email_triage_hard` — Hard
**10 emails** with competing priorities, high stakes, and nuanced judgment calls.

| Email | Correct Action | Why it's hard |
|-------|---------------|---------------|
| CTO directive: revise Phoenix go/no-go by 9am | `reply` | Multi-stakeholder, deadline |
| Resignation letter (3-year employee) | `reply` | Sensitive, transition planning needed |
| SOC: possible data breach (Tor exfil) | `forward` to CISO | 30-min escalation window |
| Employee: 2.5% raise vs $27K competing offer | `reply` | Retention risk, EQ required |
| Stripe integration down: $34K unconfirmed | `label: urgent` | Active P0, on-call unresponsive |
| Vendor: save $180K/year switching analytics | `label: normal` | Interesting but not urgent |
| Whistleblower: $2.1M accounting irregularity | `forward` to legal | Legal obligation, anonymous |
| TechCrunch interview request by 4pm | `reply` | PR opportunity + reputation risk |
| Legal reply re: non-compete clause 7.3 | `label: normal` | Reference only, no action |
| $420K ARR customer threatening churn | `reply: urgent` | Executive escalation needed |

Expected score — random agent: ~0.10 | GPT-4: ~0.60

---

## Action Space

```python
class EmailTriageAction(Action):
    action_type: str   # label | reply | forward | archive | delete | snooze | flag
    label: str | None  # urgent | normal | spam | needs_reply | archive
    reply_text: str | None   # text of reply (for reply actions)
    forward_to: str | None   # recipient (for forward actions)
    reasoning: str | None    # agent's explanation (used in grading)
```

**Valid action types:** `label`, `reply`, `forward`, `archive`, `delete`, `snooze`, `flag`

**Valid labels:** `urgent`, `normal`, `spam`, `needs_reply`, `archive`

---

## Observation Space

```python
class EmailTriageObservation(Observation):
    email: EmailData | None       # Current email to process
    inbox_size: int               # Emails remaining
    processed_count: int          # Emails processed so far
    last_action_result: str       # Feedback on last action
    score_so_far: float           # Running score [0.0–1.0]
    triaged_emails: list[dict]    # History of processed emails
    done: bool
    reward: float | None
```

### EmailData fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique email identifier |
| `subject` | str | Email subject line |
| `sender` | str | Display name |
| `sender_email` | str | Sender's email address |
| `body` | str | Full email body |
| `timestamp` | str | ISO 8601 timestamp |
| `thread_length` | int | Number of messages in thread |
| `has_attachment` | bool | Whether email has attachments |
| `is_reply` | bool | Whether this is a reply |
| `metadata` | dict | Extra context (severity, deadlines, etc.) |

---

## Reward Function

The reward function provides **dense, shaped signal** — not just binary success/failure.

| Event | Reward |
|-------|--------|
| Correct label (exact match) | `+1.0` |
| Good reply (length + key content coverage) | `+0.7–1.0` |
| Partial reply (correct type, missing content) | `+0.4–0.7` |
| Correct forward (right destination) | `+0.7–1.0` |
| Correct archive | `+1.0` |
| Delete spam (when label=spam expected) | `+0.8` |
| Delete non-spam | `0.0` |
| Flagging urgent email | `+0.4` (partial credit) |
| Snoozing non-urgent | `+0.2–0.5` |
| **Invalid action type** | `-0.1` (penalty) |
| **No-op action** | `-0.05` (penalty) |
| **Excellent episode bonus** (score ≥ 0.8) | `+0.2` |

### Episode scoring (weighted)

Final episode score is a **weighted mean** across all emails:
- `urgent` emails → weight **2.0** (higher stakes)
- `needs_reply` emails → weight **1.5**
- `normal/archive/spam` → weight **1.0**

This reflects the real cost of missing a critical email vs. a newsletter.

---

## API Reference

All endpoints are available at `http://localhost:7860` (or your deployed Space URL).

### `POST /reset`
```json
{
  "task_name": "email_triage_easy",
  "session_id": "my-session",
  "seed": null,
  "episode_id": null
}
```

### `POST /step`
```json
{
  "session_id": "my-session",
  "action_type": "label",
  "label": "urgent",
  "reply_text": null,
  "forward_to": null,
  "reasoning": "This is a production outage alert"
}
```

### `GET /state?session_id=my-session`
Returns full internal state (for evaluation/debugging).

The environment also exposes `state()` for direct programmatic access to the current typed state object.

### `GET /summary?session_id=my-session`
Returns per-email scores and final episode score.

### `GET /health`
Returns `{"status": "ok"}`.

### `GET /web`
Browser-based manual testing UI.

### `WS /ws`
WebSocket endpoint. Send JSON with `"command": "reset"` or `"command": "step"`.

---

## Setup & Usage

### Local development

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/email-triage-openenv
cd email-triage-openenv

# Install
pip install -r requirements.txt

# Run server
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload

# Run tests
pytest tests/ -v

# Run baseline inference (requires running server)
export HF_TOKEN=your_key
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
python inference.py
```

### Docker

```bash
# Build
docker build -t email-triage-openenv .

# Run
docker run -p 7860:7860 \
  -e HF_TOKEN=your_key \
  email-triage-openenv

# Verify
curl http://localhost:7860/health
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name": "email_triage_easy"}'
```

### Python client (programmatic)

```python
import requests

BASE = "http://localhost:7860"

# Reset
resp = requests.post(f"{BASE}/reset", json={"task_name": "email_triage_easy"})
obs = resp.json()["observation"]

# View first email
print(obs["email"]["subject"])
print(obs["email"]["body"])

# Take action
resp = requests.post(f"{BASE}/step", json={
    "action_type": "label",
    "label": "urgent",
    "reasoning": "Production system down — critical alert"
})
result = resp.json()
print(f"Reward: {result['reward']}")
print(f"Feedback: {result['observation']['last_action_result']}")
```

---

## Baseline Scores

Tested with `Qwen/Qwen2.5-72B-Instruct` via HuggingFace router:

| Task | Difficulty | Emails | Score |
|------|-----------|--------|-------|
| `email_triage_easy` | Easy | 5 | **0.85** |
| `email_triage_medium` | Medium | 8 | **0.68** |
| `email_triage_hard` | Hard | 10 | **0.52** |

Random agent baseline: ~0.12 across all tasks.

---

## Deploy to HuggingFace Spaces

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Select **Docker** as the SDK
3. Push this repository:
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/email-triage-openenv
   git push hf main
   ```
4. Add Secrets in Space settings:
   - `HF_TOKEN` — your HuggingFace API key

The Space will be live at `https://YOUR_USERNAME-email-triage-openenv.hf.space`

---

## OpenEnv Validation

```bash
pip install openenv-core
openenv validate .
```

Expected output:
```
✓ openenv.yaml found and valid
✓ reset() endpoint responds
✓ step() endpoint responds
✓ state() endpoint responds
✓ health endpoint returns 200
✓ 3 tasks found with graders
✓ All scores in [0.0, 1.0]
✓ Dockerfile builds successfully
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HF_TOKEN` | Yes | — | HuggingFace / API key for inference |
| `API_BASE_URL` | No | `https://router.huggingface.co/v1` | LLM API endpoint |
| `MODEL_NAME` | No | `Qwen/Qwen2.5-72B-Instruct` | Model identifier |
| `ENV_BASE_URL` | No | `http://localhost:7860` | Environment server URL (inference script) |
| `TASK_NAME` | No | all tasks | Run a single task in inference.py |
| `PORT` | No | `7860` | Server port |

---

## License

MIT License — see [LICENSE](LICENSE) for details.
