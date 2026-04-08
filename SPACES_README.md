---
title: Email Triage OpenEnv
emoji: 📧
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
tags:
  - openenv
  - reinforcement-learning
  - email
  - agent
  - evaluation
  - nlp
pinned: false
license: mit
short_description: Real-world email triage environment for AI agent training
---

# Email Triage OpenEnv

Real-world corporate email triage environment implementing the [OpenEnv](https://github.com/raun/openenv-course) specification.

**3 tasks:** easy (5 emails) → medium (8 emails) → hard (10 emails)

**API endpoints:**
- `POST /reset` — Start a new episode
- `POST /step` — Take an action
- `GET /state` — View current state
- `GET /health` — Health check
- `GET /web` — Browser UI for manual testing
- `GET /docs` — Interactive API docs

See the full README in the repository for setup instructions, action/observation space documentation, and baseline scores.
