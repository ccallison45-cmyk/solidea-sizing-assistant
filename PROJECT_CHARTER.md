# Project Charter: solidea-sizing-assistant

## Problem Statement

Solidea US customers must contact support (email or phone) to determine their correct compression garment size. The store owner manually cross-references sizing chart images on product pages with each customer's body measurements. This back-and-forth delays purchases, consumes staff time, and depresses conversion rates.

**Who is affected:** Solidea US customers shopping on solideaUS.com; the store owner and staff handling sizing inquiries.

**Current state:** Manual lookup of PNG sizing chart images per product category, communicated via email or phone. Every sizing inquiry requires multiple exchanges before the customer gets a recommendation.

## Solution Overview

A self-service sizing assistant that accepts a customer's body measurements and garment type, then instantly returns the correct Solidea size with a link to purchase. It operates through two channels:

1. **Shopify widget**: An embedded popup form on product pages that detects the product type, collects measurements, and displays the recommended size
2. **Email automation**: An n8n workflow that monitors the store inbox for sizing inquiries, parses measurements, calls the sizing API, and sends an auto-reply

Both channels are powered by the same Python/FastAPI backend that holds the sizing logic.

## Scope

### In Scope (v1)

- [ ] Sizing data extraction: Manually digitize the 5-7 PNG sizing charts into structured JSON files, organized by product type (arm sleeves, leggings, capris, knee-high socks, bras)
- [ ] Sizing API: Python FastAPI service that accepts measurements + garment type and returns the recommended size (or "between sizes" guidance)
- [ ] Shopify widget: Vanilla JavaScript popup form embedded on product pages via script tag. Detects product type and shows relevant measurement fields
- [ ] Email automation: n8n workflow that monitors the inbox, extracts measurements and product type, calls the sizing API, and sends an auto-reply with the recommendation
- [ ] Deployment: Host the FastAPI backend on a free-tier platform (Railway, Render, or Fly.io)

### Out of Scope (v1)

- Automated OCR of sizing chart images: manual extraction instead
- User accounts or saved measurement history
- Multi-language support
- Returns/exchanges sizing verification
- Integration with Shopify order or inventory data
- Custom domain or SSL for the API (use platform-provided URL)

## Users & Personas

| Persona | Role | Primary Need | Interaction Model |
|---|---|---|---|
| Customer (self-service) | Shopper on solideaUS.com | Determine correct garment size from measurements without contacting support | Popup form on product pages |
| Customer (email) | Shopper who emails the store | Get a sizing recommendation via email reply | Sends email, receives automated reply |
| Owner/Staff | Store operator | Reduce time spent on sizing inquiries; handle complex cases | Direct API access or n8n dashboard for overrides |

## Success Metrics

| Metric | Target | How Measured |
|---|---|---|
| Reduction in sizing inquiries | 50% fewer sizing-related emails/calls within 30 days of launch | Compare support ticket count before vs. after |
| Conversion rate improvement | Measurable increase in product page conversion | Shopify analytics: product page add-to-cart rate |
| Widget usage | 100+ sizing lookups per week | API request logs |

## Constraints & Assumptions

### Constraints

- **Timeline**: ASAP, target 1-2 weeks to MVP
- **Budget**: Free-tier infrastructure only; no paid APIs or services
- **Compliance**: Minimal - body measurements are not PII; no data stored beyond request logs
- **Infrastructure**: Shopify storefront (cannot modify Shopify backend); external API hosting required

### Assumptions

- Sizing charts on solideaUS.com are accurate and current
- Product types map cleanly to distinct sizing chart categories
- Measurements from chart images can be digitized into clear numeric ranges
- Free-tier hosting provides sufficient uptime and performance for expected traffic
- Customers are willing to self-measure using standard body measurement instructions

## Timeline

| Milestone | Target | Deliverables |
|---|---|---|
| Project Setup | Day 1 | Repository, dependencies, CI pipeline |
| Sizing Data Extraction | Days 2-3 | All 5 product type JSON files, validated schema |
| Sizing API | Days 3-5 | Working FastAPI endpoint with tests |
| Shopify Widget | Days 5-7 | Widget live on product pages |
| Email Automation | Days 7-9 | n8n workflow processing inbox |
| Deployment & Go-Live | Days 9-10 | Production API, widget installed, email automation running |

## Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Sizing charts have ambiguous or overlapping ranges | Medium | High | Add "between sizes" logic; flag edge cases for manual review |
| Shopify CSP blocks external API calls from the widget | Low | High | Configure CORS headers; if blocked, investigate Shopify App Proxy |
| Free-tier hosting has cold start latency | Medium | Low | Use keep-alive pings via UptimeRobot/cron-job.org |
| Owner needs to update sizing data when products change | Medium | Medium | Document JSON format clearly; provide editing guide in runbook |
| n8n cannot reliably parse unstructured sizing emails | Medium | Medium | Add fallback: forward unparseable emails to owner instead of auto-replying |
