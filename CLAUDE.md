# CLAUDE.md -- solidea-sizing-assistant

## Project Identity

- **Name**: solidea-sizing-assistant
- **Description**: Self-service sizing tool that helps Solidea US customers find their correct compression garment size based on body measurements
- **Primary Language**: Python
- **Interaction Model**: Web widget (Shopify embed) + REST API + email automation (n8n)
- **Repository**: local (to be pushed to GitHub)

## Tooling & System Map

Every tool in this project was selected using the Tool Selection Rules. No tool is here "by default."

| Tool | Category | Why Selected | Scope of Use | Data Allowed | Risks | Mitigations |
|---|---|---|---|---|---|---|
| Python 3.12 | Language | Data processing (sizing logic) + API server; owner comfortable with Python | All backend code: API, sizing logic, data loading, tests | Body measurements (non-PII), sizing chart data | Dependency management | uv for lockfile, pin versions in pyproject.toml |
| FastAPI | Web Framework | Python + API-only trigger; Pydantic validation ideal for measurement inputs | API server, request/response handling | Measurement inputs, size recommendations | Learning curve | Minimal usage: single endpoint |
| JavaScript (vanilla) | Language | Shopify frontend requires JS; no framework needed for a single popup form | Shopify product page widget only | Product type identifier, user-entered measurements | Browser compatibility | ES5-compatible syntax; test on major browsers |
| n8n | Orchestration | 3+ integrations (email, API, SMTP), webhook triggers, non-developer owner can modify | Email inbox monitoring, API calls, auto-reply sending | Email content, parsed measurements, sizing results | Workflow breakage on n8n updates | Pin n8n version; document workflow steps |
| JSON files | Data Storage | Static read-only dataset under 1MB; no concurrent writes; no database trigger met | Sizing chart data per product type (5 files) | Measurement-to-size mappings | Manual editing errors | Validate JSON on startup; JSON schema |
| pytest | Testing | Python project auto-selects pytest | All backend test files | Test fixtures only | None significant | Keep tests fast |
| Ruff | Linting | Python project auto-selects Ruff | All Python files | Source code only | None significant | Pin version |
| GitHub Actions | CI/CD | GitHub-hosted repo, standard choice | Lint + test on push/PR | Source code, test results | Free tier minute limits | Minimal pipeline |
| Railway/Render | Deployment | Free-tier PaaS sufficient for low-traffic API | Production API hosting | API requests/responses | Cold starts, free-tier limits | Health check pinger |

## When to Use Python

Python is the primary language for this project. Use it for:
- All backend API code (FastAPI routes, request handling, response formatting)
- Sizing logic (measurement-to-size matching algorithms)
- Data loading and validation (reading and parsing JSON sizing files)
- Tests (pytest)
- Utility scripts (data validation, sizing chart import helpers)

Do NOT use Python for:
- The Shopify frontend widget -- use vanilla JavaScript instead
- Email automation workflow logic -- use n8n's visual workflow editor instead
- Shopify theme modifications -- use Liquid/HTML as required by Shopify

Python version: 3.12+
Package manager: uv (with pyproject.toml)

## When to Use MCP

MCP is **not used** in this project. No MCP servers are configured or authorized.

If a future need arises:
1. Document the need in an ADR.
2. Verify all activation criteria from the MCP Policy.
3. Update this CLAUDE.md with the allowed servers table.

## Commands

```bash
# Install dependencies
uv sync

# Start development server
uv run uvicorn app.main:app --reload --port 8000

# Run tests
uv run pytest

# Run linter/formatter
uv run ruff check . && uv run ruff format .

# Run type checker (optional)
uv run mypy app/
```

Production deployment happens via Git push -- Railway/Render auto-deploys from the main branch.

## Invariants

These must **always** be true. Violating any invariant is a blocking issue.

1. Every product type in `/data` must have a valid JSON file with at least one size entry.
2. The sizing API must never return HTTP 500 for valid measurement inputs -- always return a recommendation or a clear "out of range" message.
3. All sizing JSON files must conform to the project's JSON schema (validated at application startup).
4. The widget must never send measurements to any endpoint other than this project's own API.
5. No customer measurements are persisted to disk or database -- the API is stateless.
6. All tests pass before any merge to main.
7. No secrets in code, config files, or logs.
8. `.env.example` stays in sync with actual environment variables used.

## How Future Chats Must Behave

When working in this project, you (Claude or any AI assistant) must:

1. **Read this CLAUDE.md first** before making any changes.
2. **Follow the Tooling & System Map.** Do not introduce tools not listed in the table without creating an ADR and updating this file.
3. **Respect the invariants.** If a proposed change would violate an invariant, stop and flag it.
4. **Use the specified language.** Python for backend, JavaScript for widget, n8n for workflows. Do not switch without justification.
5. **Run tests after changes.** Use `uv run pytest`. Do not skip.
6. **Do not commit secrets.** Check `.env.example` for the pattern. Real values go in `.env` (gitignored).
7. **Keep TASKS.md updated.** Mark tasks complete as you finish them. Add new tasks as discovered.
8. **Create ADRs for significant decisions.** Any new tool, major refactor, or architecture change gets an ADR in `docs/decisions/`.
9. **Prefer editing over creating.** Modify existing files rather than creating new ones, unless the change is clearly a new module.
10. **Ask when uncertain.** If requirements are ambiguous, ask rather than assume.
