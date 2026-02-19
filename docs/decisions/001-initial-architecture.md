# ADR-001: Initial Architecture and Tool Choices

## Status

Accepted

## Date

2026-02-19

## Context

The Solidea Sizing Assistant needs to serve sizing recommendations through two channels: a Shopify-embedded widget and an automated email responder. The system must be built quickly (1-2 weeks), run on free infrastructure, and be maintainable by a solo owner who is comfortable with Python and n8n but is not a professional developer.

Key forces:
- Sizing data is static (5-7 charts, rarely changes)
- No database needed (read-only JSON lookup, under 1MB total)
- Must embed in Shopify without building a custom Shopify app (script tag injection)
- Email automation must be modifiable by a non-developer (visual workflow editor)
- Budget is zero for infrastructure

## Decision

### 1. Backend: Python 3.12 + FastAPI

- Single API endpoint: `POST /api/v1/size-recommendation`
- Accepts: `{ "product_type": "leggings", "measurements": { "height_cm": 170, "weight_kg": 65 } }`
- Returns: `{ "recommended_size": "M", "confidence": "exact", "notes": "" }`
- Sizing data stored as JSON files in a `/data` directory, loaded into memory at startup
- Package management via `uv` with `pyproject.toml`

### 2. Frontend widget: Vanilla JavaScript

- Injected via Shopify script tag (no build step, no framework)
- Reads product type from the page (product tags, metafields, or URL patterns)
- Shows measurement input fields specific to that product type
- Calls the FastAPI backend via `fetch()`
- Single popup form UX

### 3. Email automation: n8n workflow

- Trigger: IMAP email poll on the store inbox
- Steps: Parse email body for measurements and product type -> call sizing API -> format reply -> send email
- Fallback: forward to owner if the email cannot be parsed
- Hosted on n8n cloud or self-hosted

### 4. Data format: JSON files per product type

- `data/arm-sleeves.json`, `data/leggings.json`, `data/capris.json`, `data/socks.json`, `data/bras.json`
- Schema: array of size entries with measurement ranges (`{ size, measurements: { field: { min, max } } }`)
- Validated at application startup

### 5. Deployment: Railway or Render free tier

- Single container running the FastAPI app
- Widget JS served as a static file from the same service
- Auto-deploys from GitHub main branch

## Alternatives Considered

### Shopify-native Liquid/metafields approach
- **Pros**: No external hosting needed, no CORS issues
- **Cons**: Cannot do complex sizing logic in Liquid; hard to maintain conditional ranges per product type; would not support email automation
- **Why rejected**: Sizing logic requires conditional numeric range matching per product type, which is impractical in Liquid templates

### Node.js/Express backend
- **Pros**: Single language for frontend and backend
- **Cons**: Owner is more comfortable with Python; FastAPI has better data validation (Pydantic); Python matches the data-processing nature of the sizing logic
- **Why rejected**: Python is the owner's preferred language and matches TOOL_SELECTION_RULES triggers for data processing

### Google Sheets as the data backend
- **Pros**: Owner can edit sizing data in a familiar interface
- **Cons**: Adds API latency, rate limiting concerns, dependency on Google API availability
- **Why rejected**: JSON files are simpler, faster, have no external dependency; data changes are infrequent enough to edit JSON directly

## Consequences

### Positive
- Simple architecture with minimal moving parts (API + widget + n8n workflow)
- Owner can modify n8n workflows without code changes
- Free-tier hosting is sufficient for expected traffic volume
- JSON data files are version-controlled and easily auditable
- Stateless API means zero data storage compliance burden

### Negative
- Cross-origin requests from Shopify to the external API require CORS configuration
- Cold starts on free-tier platforms may add 1-3 seconds on first request
- Sizing data updates require editing JSON files and redeploying

### Mitigations
- Configure CORS to allow solideaUS.com origin specifically
- Implement a health check endpoint with external pinger (UptimeRobot) to keep service warm
- If CORS proves problematic on Shopify, investigate Shopify App Proxy as an alternative routing mechanism
- Document JSON editing process clearly in the owner runbook
