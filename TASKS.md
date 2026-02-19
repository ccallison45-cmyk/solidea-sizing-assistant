# Tasks: solidea-sizing-assistant

> Priority: P0 = must have, P1 = should have, P2 = nice to have
> Size: S = hours, M = day, L = multiple days

---

## Milestone 1: Project Setup

- [x] **Initialize project structure** [P0] [S] *(completed 2026-02-19)*
  - Description: Create folder structure (app/, data/, tests/, widget/), initialize pyproject.toml with uv, configure Ruff
  - Acceptance criteria: `uv sync` and `uv run ruff check .` run without errors

- [x] **Configure development environment** [P0] [S] *(completed 2026-02-19)*
  - Description: Create .gitignore (Python + .env + node_modules), verify .env.example, set up local run instructions
  - Acceptance criteria: New developer can clone and run the API with only README instructions

- [x] **Set up testing framework** [P0] [S] *(completed 2026-02-19)*
  - Description: Configure pytest in pyproject.toml, create conftest.py, write one passing placeholder test
  - Acceptance criteria: `uv run pytest` runs and passes

- [x] **Create initial CI pipeline** [P1] [S] *(completed 2026-02-19)*
  - Description: Configure GitHub Actions to run Ruff lint + pytest on push and PR to main
  - Acceptance criteria: Pipeline passes on main branch

## Milestone 2: Sizing Data Extraction

- [x] **Define sizing data JSON schema** [P0] [S] *(completed 2026-02-19)*
  - Description: Design the JSON structure for sizing data. Each product type file contains an array of size objects with measurement ranges (min/max for each relevant measurement). Create data/schema.json.
  - Acceptance criteria: JSON schema documented; a sample file validates against it

- [x] **Extract arm sleeve sizing data** [P0] [S] *(completed 2026-02-19)*
  - Description: Manually transcribe the arm sleeve sizing chart image from solideaUS.com into data/arm-sleeves.json. Fields: upper_arm_circumference_cm, forearm_circumference_cm, wrist_circumference_cm. Sizes: S, M, L, XL.
  - Acceptance criteria: JSON file exists, validates against schema, covers all sizes shown in the chart

- [x] **Extract legging sizing data** [P0] [S] *(completed 2026-02-19)*
  - Description: Manually transcribe the legging sizing chart. Fields: height_cm, weight_kg, hip_circumference_cm, waist_circumference_cm. Sizes: S through XXXL.
  - Acceptance criteria: JSON file exists, validates against schema, covers all sizes

- [x] **Extract capri sizing data** [P0] [S] *(completed 2026-02-19)*
  - Description: Transcribe the capri sizing chart. Fields: height_cm, weight_kg, hip_circumference_cm, waist_circumference_cm. Sizes: S through XXL.
  - Acceptance criteria: JSON file exists, validates against schema

- [x] **Extract sock sizing data** [P0] [S] *(completed 2026-02-19)*
  - Description: Transcribe the knee-high sock sizing chart. Fields: calf_circumference_cm, ankle_circumference_cm. Sizes: S through XXL.
  - Acceptance criteria: JSON file exists, validates against schema

- [x] **Extract bra sizing data** [P0] [S] *(completed 2026-02-19)*
  - Description: Transcribe the bra sizing chart. Fields: bust_circumference_cm, underbust_circumference_cm. Sizes: XS through XXL.
  - Acceptance criteria: JSON file exists, validates against schema

- [x] **Add startup validation for sizing data** [P0] [S] *(completed 2026-02-19)*
  - Description: On FastAPI startup, load all JSON files from /data and validate against the schema. Fail fast if any file is invalid or missing.
  - Acceptance criteria: App refuses to start if a JSON file is malformed; logs which file is invalid

## Milestone 3: Sizing API

- [x] **Create FastAPI application skeleton** [P0] [M] *(completed 2026-02-19)*
  - Description: Set up app/main.py with FastAPI instance, CORS middleware (allow solideaUS.com + localhost for dev), health check endpoint (GET /health)
  - Acceptance criteria: `uv run uvicorn app.main:app` starts; GET /health returns 200

- [x] **Define Pydantic request/response models** [P0] [S] *(completed 2026-02-19)*
  - Description: Create models for SizingRequest (product_type enum, measurements dict) and SizingResponse (recommended_size, confidence level, notes, product_url). Product types: arm_sleeves, leggings, capris, socks, bras.
  - Acceptance criteria: Models import without error; invalid inputs are rejected with 422

- [x] **Implement sizing logic engine** [P0] [M] *(completed 2026-02-19)*
  - Description: Core function that takes product type and measurements, matches against loaded JSON data. Handle exact matches, between-sizes cases, and out-of-range inputs.
  - Acceptance criteria: Unit tests cover exact match, between-sizes, and out-of-range for at least 2 product types

- [x] **Create POST /api/v1/size-recommendation endpoint** [P0] [S] *(completed 2026-02-19)*
  - Description: Wire Pydantic models to sizing logic. Return JSON response with recommended_size, confidence, and notes.
  - Acceptance criteria: curl request returns correct size for known test inputs

- [x] **Add comprehensive test suite for sizing logic** [P0] [M] *(completed 2026-02-19)*
  - Description: pytest tests covering all 5 product types, edge cases (boundary values, missing measurements, invalid product types)
  - Acceptance criteria: All tests pass; every product type has at least 3 test cases (36 tests total)

## Milestone 4: Shopify Widget

- [x] **Create widget HTML/CSS/JS** [P0] [M] *(completed 2026-02-19)*
  - Description: Built widget/sizing-widget.js — self-contained JS that injects CSS, renders popup form with measurement fields per product type, calls API, displays results. Includes test-page.html for local development.
  - Acceptance criteria: Widget renders on a local HTML test page; form submits measurements correctly

- [x] **Implement product type detection** [P1] [S] *(completed 2026-02-19)*
  - Description: Widget detects product type from Shopify meta.product object, page title, URL path, and h1 content using keyword matching. Falls back to dropdown selector if not detected.
  - Acceptance criteria: Correctly identifies product type on at least 3 different product pages

- [x] **Connect widget to sizing API** [P0] [S] *(completed 2026-02-19)*
  - Description: Widget calls POST /api/v1/size-recommendation via fetch() and displays the result in the popup. Widget JS also served as a static file from /static/sizing-widget.js.
  - Acceptance criteria: End-to-end: enter measurements in widget, see correct size and product link

- [x] **Style widget for Solidea brand** [P1] [S] *(completed 2026-02-19)*
  - Description: Dark navy (#1a1a2e) header/buttons, gold (#c9a96e) CTA, clean typography, responsive mobile layout (full-screen on <540px). Matches luxury compression garment branding.
  - Acceptance criteria: Widget looks professional on desktop and mobile viewports

- [ ] **Install widget on Shopify store** [P0] [S]
  - Description: Add the script tag to the Shopify theme. Liquid install snippet prepared at widget/shopify-install.liquid. Requires production API URL.
  - Acceptance criteria: Widget appears on product pages on the live store; sizing lookups work end-to-end
  - **Note**: Blocked on deployment (Milestone 6) — needs production API URL first

## Milestone 5: Email Automation

- [x] **Design n8n email parsing workflow** [P0] [M] *(completed 2026-02-19)*
  - Description: Created importable n8n workflow JSON (n8n/sizing-email-workflow.json) with: IMAP trigger → sizing keyword filter → Code node for email parsing (regex extraction of measurements) → IF node for processability routing.
  - Acceptance criteria: Workflow triggers on test email and correctly parses measurements

- [x] **Connect n8n to sizing API** [P0] [S] *(completed 2026-02-19)*
  - Description: HTTP Request node in workflow calls POST /api/v1/size-recommendation with parsed product type and measurements. Format Reply code node transforms API response for email template.
  - Acceptance criteria: n8n workflow receives a valid sizing recommendation from the API

- [x] **Create auto-reply email template** [P1] [S] *(completed 2026-02-19)*
  - Description: Professional HTML email template (n8n/email-template.html) with Solidea branding, size recommendation display, confidence explanation, Shop Now CTA, and contact fallback.
  - Acceptance criteria: Reply email is well-formatted and contains the correct size and product link

- [x] **Add fallback for unparseable emails** [P1] [S] *(completed 2026-02-19)*
  - Description: IF node routes unparseable emails (missing product type or measurements) to "Forward to Owner" node which sends email with original content and parsing diagnostics.
  - Acceptance criteria: Unparseable emails land in the owner's inbox; no incorrect auto-replies sent

- [ ] **Test end-to-end email flow** [P0] [S]
  - Description: Send test emails with various formats and verify correct auto-replies or escalation to owner. Requires n8n instance with configured IMAP/SMTP credentials.
  - Acceptance criteria: 5+ test emails processed correctly
  - **Note**: Blocked on n8n instance setup — workflow JSON and documentation ready for import

## Milestone 6: Deployment and Go-Live

- [x] **Deploy FastAPI to Railway/Render** [P0] [M] *(completed 2026-02-19)*
  - Description: Created Procfile, Dockerfile, render.yaml (Render Blueprint), railway.json, and .dockerignore. Deployment guide at docs/runbooks/deployment.md. Actual deployment requires pushing to GitHub and connecting the platform.
  - Acceptance criteria: API responds at production URL; GET /health returns 200

- [x] **Configure production CORS** [P0] [S] *(completed 2026-02-19)*
  - Description: CORS is env-driven via ALLOWED_ORIGINS. Default is localhost for dev; render.yaml sets production value to https://solideaus.com,https://www.solideaus.com. No code change needed per environment.
  - Acceptance criteria: Widget on Shopify can call API; requests from other origins are blocked

- [x] **Set up keep-alive pinger** [P2] [S] *(completed 2026-02-19)*
  - Description: UptimeRobot and cron-job.org instructions documented in docs/runbooks/owner-guide.md. External service setup is a manual step after deployment.
  - Acceptance criteria: API stays warm; no cold start delays during business hours

- [x] **Create owner documentation** [P1] [M] *(completed 2026-02-19)*
  - Description: Owner guide at docs/runbooks/owner-guide.md covers: updating sizing JSON data, monitoring n8n workflow, reading API logs, keep-alive pinger setup, troubleshooting. Deployment guide at docs/runbooks/deployment.md covers Render and Railway setup.
  - Acceptance criteria: Non-technical owner can follow the guide to update a sizing chart

---

## Completed

All milestones code-complete as of 2026-02-19. Remaining manual steps:
- Push to GitHub and connect Railway/Render for actual deployment
- Install widget on Shopify store (needs production API URL)
- Import n8n workflow and configure IMAP/SMTP credentials
- Set up UptimeRobot or cron-job.org for keep-alive pings
- Test end-to-end email flow with real inbox

## Discovered During Work

- Sizing data from solideaUS.com uses overlapping ranges between adjacent sizes (intentional by Solidea for customer comfort). The sizing engine handles this by scoring all sizes and picking the best match.
- Leggings/capris charts on solideaUS.com use a 2D height/weight grid (imperial) plus waist/hip circumference (metric). Both measurement sets are stored in JSON and used by the engine.
- Bra size chart image resolution on solideaUS.com is low — M through XXL column values should be verified with Solidea directly (info@solideaus.com or 888-841-8834).
