# Personalized GitHub Repository Agent (Web)

A web-based AI agent for repository review and GitHub drafting workflows.

## Implemented Required Patterns

- **Planning pattern**: `PlannerAgent` decides action (`create_issue`, `create_pr`, `no_action`) after review.
- **Tool use pattern**: Uses real tools via `git diff`, `git fetch`, file reads, and live GitHub API fetch/create calls.
- **Reflection pattern**: `GatekeeperAgent` emits a reflection artifact (`PASS`/`FAIL`) checking unsupported claims, missing evidence, missing tests, and policy checks.
- **Multi-agent pattern**: Explicit role classes:
  - `ReviewerAgent`
  - `PlannerAgent`
  - `WriterAgent`
  - `GatekeeperAgent`

## Core Tasks Covered

### Task 1 — Review Changes
- Inputs:
  - Base branch (`main`, etc.) or
  - Commit range (`HEAD~3..HEAD`)
- Outputs:
  - Change category
  - Risk level (`low`/`medium`/`high`)
  - Evidence from diff + file reads
  - Planner decision with justification

### Task 2 — Draft + Create Issue/PR (Human Approval Required)
- Draft sources:
  - From review (`source=review`)
  - From explicit instruction (`source=instruction`)
- Draft includes required sections:
  - Issue: title, problem, evidence, acceptance criteria, risk
  - PR: title, summary, files affected, behavior change, test plan, risk
- Creation rule:
  - Draft shown first
  - Explicit approval required (`Approve YES`)
  - Rejection aborts safely (`Approve NO`)

### Task 3 — Improve Existing Issue/PR
- Fetches existing issue/PR from GitHub
- Produces critique first (missing clarity, vague language, missing criteria)
- Produces improved structured rewrite suggestion (no silent update)

## Project Structure

```
personalized_github_repo_agent/
├── app.py
├── requirements.txt
├── .env.example
├── core/
│   ├── config.py
│   ├── tools.py
│   ├── llm.py
│   ├── state.py
│   └── agents.py
├── templates/
│   └── index.html
└── static/
    ├── app.js
    └── styles.css
```

## Setup

1. Create environment variables:

```bash
copy .env.example .env
```

2. Set required GitHub values in `.env`:
- `GITHUB_OWNER`
- `GITHUB_REPO`
- `GITHUB_TOKEN`

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run app:

```bash
python app.py
```

5. Open:

- `http://127.0.0.1:5055`

## API Endpoints

- `POST /api/review`
  - body: `{ "base_branch": "main" }` or `{ "commit_range": "HEAD~3..HEAD" }`
- `POST /api/draft`
  - body: `{ "kind": "issue|pr", "source": "review|instruction", ... }`
- `POST /api/approve`
  - body: `{ "draft_id": "drf_xxx", "approve": true|false }`
- `POST /api/improve`
  - body: `{ "kind": "issue|pr", "number": 42 }`

## Notes

- Deploy key support is available through `AGENT_DEPLOY_KEY_PATH` for git SSH operations.
- PR creation requires the `head` branch to already exist on remote.
- Ollama is optional (`USE_OLLAMA=0` fallback), but enabled by default for better writing quality.
