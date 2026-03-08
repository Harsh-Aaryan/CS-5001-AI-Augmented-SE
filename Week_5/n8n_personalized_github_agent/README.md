# n8n Personalized GitHub Agent (Local)

This reproduces the `personalized_github_repo_agent` workflow in **local n8n** with the same core actions:

- `review`: analyze repo changes and return plan (`create_issue`, `create_pr`, `no_action`)
- `draft`: generate structured Issue/PR draft + reflection checks
- `approve`: human approval gate that creates GitHub Issue/PR only on explicit approval
- `improve`: critique and rewrite an existing Issue/PR draft structure

## What You Will Build

An n8n workflow that acts as a multi-agent GitHub assistant. It:

- Reviews code changes and returns a planner decision (`create_issue`, `create_pr`, `no_action`)
- Drafts GitHub Issues and Pull Requests with a mandatory human approval step before creation
- Improves existing GitHub Issues or PRs by generating critique + structured rewrite suggestions

## What This Version Implements

- Planning pattern: deterministic planner after review
- Tool use pattern: live GitHub API compare/fetch/create operations
- Reflection pattern: PASS/FAIL checks before create
- Multi-agent pattern: encoded in one router node with role-equivalent logic blocks

## Folder Structure

```text
n8n_personalized_github_agent/
├── .env.example
├── package.json
└── workflows/
    └── personalized_github_multi_agent.json
```

## 1) Configure Environment

Copy `.env.example` to `.env` and set values:

- `GITHUB_OWNER`
- `GITHUB_REPO`
- `GITHUB_TOKEN`
- optional: `AGENT_BASE_BRANCH`, `AGENT_HEAD_BRANCH`

## 2) Start n8n Locally

```bash
npm install
```

PowerShell (from project folder):

```powershell
$env:N8N_COMMUNITY_PACKAGES_ENABLED='false'
npm run start
```

PowerShell (from any folder):

```powershell
$env:N8N_COMMUNITY_PACKAGES_ENABLED='false'
npm --prefix "d:\Documentss\5001\CS-5001-AI-Augmented-SE\Week_5\n8n_personalized_github_agent" run start
```

n8n editor: `http://localhost:5678`

## 3) Import Workflow

```bash
npm run import:workflow
```

Then open n8n UI and activate the workflow.

## 4) Endpoint

Single endpoint:

- `POST /webhook/personalized-github-agent`

The action is selected by request body field `action`:

- `review`
- `draft`
- `approve`
- `improve`

## API Examples

### Review

```json
{
  "action": "review",
  "base_branch": "main",
  "head_branch": "feature/my-change"
}
```

Alternative:

```json
{
  "action": "review",
  "commit_range": "main...feature/my-change"
}
```

### Draft from Review

```json
{
  "action": "draft",
  "kind": "issue",
  "source": "review",
  "review_id": "rvw_..."
}
```

### Draft from Instruction

```json
{
  "action": "draft",
  "kind": "pr",
  "source": "instruction",
  "instruction": "Improve error handling in GitHub gateway and update docs.",
  "base_branch": "main",
  "head_branch": "feature/error-handling"
}
```

### Approve / Reject

```json
{
  "action": "approve",
  "draft_id": "drf_...",
  "approve": true
}
```

Reject:

```json
{
  "action": "approve",
  "draft_id": "drf_...",
  "approve": false
}
```

### Improve Existing Issue or PR

```json
{
  "action": "improve",
  "kind": "issue",
  "number": 42
}
```

## Notes

- This local n8n version persists review/draft state in workflow static data.
- For PR creation, ensure `head_branch` exists remotely.
- This variant is intentionally deterministic and does not require OpenAI/Ollama.

## Troubleshooting: "Execute does nothing"

This workflow starts with a **Webhook** trigger. So clicking Execute will wait for an HTTP request.

- `webhook-test` URL works only after clicking **Listen for test event**, and only for test mode calls.
- `webhook` URL works when the workflow is **Active**.

Quick production test (PowerShell):

```powershell
$body = @{
  action = 'draft'
  kind = 'issue'
  source = 'instruction'
  instruction = 'Smoke test'
} | ConvertTo-Json

Invoke-RestMethod \
  -Uri 'http://localhost:5678/webhook/personalized-github-agent' \
  -Method Post \
  -ContentType 'application/json' \
  -Body $body
```
