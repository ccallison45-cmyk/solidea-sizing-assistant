# n8n Email Automation Workflow v2

Renovated workflow that auto-processes sizing inquiry emails for Solidea US compression garments.

## Architecture

```
[Config] → [Gmail Trigger] → [Reply Chain Check] → [Smart Filter] → [Parse Email]
  → [Has Processable Product?]
    ├── YES → [Prepare API Request] → [Call Sizing API] → [API Success?]
    │         ├── YES → [Format Reply] → [Create Draft for Review] → [Log to Sheet]
    │         └── NO  → [Retry API Call] → [Retry Success?]
    │                   ├── YES → [Format Reply] → (same as above)
    │                   └── NO  → [Forward API Error to Owner]
    └── NO  → [Missing Measurements?]
              ├── YES → [Format Follow-up] → [Send Follow-up Draft] → [Log to Sheet]
              └── NO  → [Forward to Owner] → [Log to Sheet]
```

**24 nodes total** with Google Sheets logging on every path.

## What's New in v2

| Feature | v1 | v2 |
|---|---|---|
| Email trigger | IMAP polling | Gmail OAuth trigger |
| Email sending | SMTP | Gmail OAuth |
| Product detection | Generic keywords | Real Solidea product catalog names with word-boundary regex |
| Measurement parsing | "keyword: number cm" only | Natural language, feet/inches, lbs, number words |
| Unit conversion | None | inches→cm, lbs→kg, feet+inches→cm |
| Error handling | None (silent failure) | Retry once, then forward to owner with error details |
| Reply chain detection | None | Checks for auto-reply signatures + self-send loops |
| Filter accuracy | Broad ("size", "fit") | Excludes orders, shipping, unsubscribe; uses sizing-specific phrases |
| Missing measurements | Forward to owner | Sends follow-up email asking for specific measurements needed |
| Confirmation | Auto-send immediately | Creates Gmail draft for owner review before sending |
| Logging | None | Google Sheets logging (timestamp, email, product, size, confidence, action) |
| Plain text fallback | No | Yes (both HTML and plain text generated) |
| IF node conditions | Broken boolean check | Proper typeVersion 2 boolean filter conditions |
| Multi-product | No | Detects multiple products in one email |

## Setup Instructions

### Prerequisites

- An n8n instance (cloud or self-hosted)
- A Gmail account with OAuth2 configured in n8n (for the Solidea inbox)
- A Google Sheets account with OAuth2 configured in n8n (for logging)
- The Sizing API deployed at `https://web-production-41ce7.up.railway.app`

### Step 1: Create Google Sheet for Logging

1. Create a new Google Sheet
2. Name the first sheet tab **"Sizing Log"**
3. Add these column headers in Row 1:
   - A: `Timestamp`
   - B: `Customer Email`
   - C: `Customer Name`
   - D: `Product Type`
   - E: `Measurements`
   - F: `Recommended Size`
   - G: `Confidence`
   - H: `Action`
   - I: `Notes`
4. Copy the Sheet ID from the URL (the long string between `/d/` and `/edit`)

### Step 2: Set Up n8n Credentials

Create these credentials in n8n (**Settings → Credentials**):

**Gmail OAuth2:**
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Add `https://your-n8n-instance.com/rest/oauth2-credential/callback` as authorized redirect URI
4. In n8n, create a "Gmail OAuth2 API" credential with the Client ID and Secret
5. Click "Connect" and authorize the Solidea inbox

**Google Sheets OAuth2:**
1. Use the same OAuth app or create a separate one
2. Enable the Google Sheets API in your Google Cloud project
3. In n8n, create a "Google Sheets OAuth2 API" credential
4. Click "Connect" and authorize

### Step 3: Import the Workflow

1. Open your n8n instance
2. Go to **Workflows → Import from File**
3. Select `sizing-email-workflow.json`
4. The workflow will be imported in inactive state

### Step 4: Configure Placeholders

After importing, update these values:

1. **Config node** (first node):
   - `apiBaseUrl`: Already set to `https://web-production-41ce7.up.railway.app` — update if your API URL changes
   - `ownerEmail`: Already set to `info@solideaus.com` — update if different
   - `sheetId`: Replace `REPLACE_WITH_GOOGLE_SHEET_ID` with your Google Sheet ID from Step 1

2. **Gmail nodes** (Gmail Trigger, Create Draft for Review, Send Follow-up Draft, Forward to Owner, Forward API Error to Owner):
   - Select your Gmail OAuth2 credential from the dropdown in each node

3. **Google Sheets nodes** (Log to Sheet, Log Follow-up to Sheet, Log Forward to Sheet):
   - Select your Google Sheets OAuth2 credential from the dropdown in each node

### Step 5: Activate

1. Click **Save**
2. Toggle the workflow to **Active**
3. The workflow will poll for new emails every 2 minutes

## How It Works

### Email Processing Pipeline

1. **Gmail Trigger** polls every 2 minutes for new inbox emails
2. **Reply Chain Check** drops emails that are replies to previous auto-replies (prevents loops)
3. **Smart Filter** determines if the email is a sizing inquiry (excludes orders, shipping notifications, etc.)
4. **Parse Email** extracts:
   - Product type (mapped from real Solidea product names)
   - Body measurements (with unit conversion from inches/lbs/feet)
   - Which measurements are present vs. missing for each product

### Routing Logic

- **All measurements present**: Calls the sizing API → creates a Gmail draft with the recommendation for your review
- **Product detected, measurements incomplete**: Creates a follow-up draft asking for the specific missing measurements
- **No product detected**: Forwards the email to the owner inbox for manual handling
- **API failure**: Retries once, then forwards to owner with error details

### Measurement Parsing Examples

The parser handles all of these formats:
- `"I'm 5'7 and 140 lbs"` → height_cm: 170.18, weight_kg: 63.5
- `"height: 170cm, weight: 65kg"` → height_cm: 170, weight_kg: 65
- `"my bust is 95 and underbust is 77"` → bust_circumference_cm: 95, underbust_circumference_cm: 77
- `"waist 28 inches, hips 38 inches"` → waist_circumference_cm: 71.12, hip_circumference_cm: 96.52
- `"calf: 14in, ankle: 9in"` → calf_circumference_cm: 35.56, ankle_circumference_cm: 22.86

### Product Name Mapping

| Customer might say | Maps to API type |
|---|---|
| arm sleeve, armband, gauntlet, compression arm | `arm_sleeves` |
| legging, tights, pantyhose, bike short, compression short, men's brief | `leggings` |
| capri, capris | `capris` |
| sock, knee-high, ankle sock, mid-calf, calf sleeve, thigh high | `socks` |
| bra, braless top, tank top, compression top, bodysuit | `bras` |

## Test Emails

Send these to the monitored inbox to verify each workflow path.

### Path 1: Full auto-reply (draft created)

```
Subject: What size leggings should I get?
Body: Hi, I'm 5'7 and weigh 140 lbs. My waist is 28 inches and hips are 38 inches.
Can you recommend a size for your compression leggings?
```
**Expected**: Draft created with size recommendation.

```
Subject: Arm sleeve sizing help
Body: My bicep measures 33cm, wrist is 17cm, and arm length is 58cm.
```
**Expected**: Draft created with arm sleeve size recommendation.

```
Subject: Bra size question
Body: Bust: 95cm, underbust: 77cm. What size compression bra should I order?
```
**Expected**: Draft created with bra size recommendation.

```
Subject: Need socks size
Body: My calf is about 14 inches and ankle is 9 inches.
```
**Expected**: Draft created with socks size recommendation (inches converted to cm).

### Path 2: Follow-up (missing measurements)

```
Subject: Leggings sizing
Body: I'm 170cm tall and weigh 65kg. What size legging do I need?
```
**Expected**: Follow-up draft asking for waist and hip measurements.

```
Subject: Help with arm sleeve size
Body: My bicep is 33cm. What size arm sleeve do I need?
```
**Expected**: Follow-up draft asking for wrist circumference and arm length.

### Path 3: Forward to owner (no product detected)

```
Subject: Sizing question
Body: What size should I get? I usually wear a medium in other brands.
```
**Expected**: Forwarded to owner (no product type detected).

```
Subject: General question
Body: Do you ship to Canada?
```
**Expected**: Filtered out by Smart Filter (no sizing intent) — never reaches Parse Email.

### Path 4: Filtered out (not a sizing inquiry)

```
Subject: Order #12345 confirmation
Body: Thank you for your order! Your tracking number is...
```
**Expected**: Excluded by Smart Filter (order confirmation).

```
Subject: Your order has shipped
Body: Great news! Your Solidea leggings are on their way.
```
**Expected**: Excluded by Smart Filter (shipping notification).

### Path 5: Reply chain detection

```
Subject: Re: Your Solidea Leggings Size Recommendation
Body: Thanks! I ordered the medium. Also, what about your capris?
```
**Expected**: Dropped by Reply Chain Check (contains "Your Solidea" from previous auto-reply).

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| Workflow not triggering | Gmail credential expired or workflow inactive | Re-authorize Gmail credential; toggle workflow active |
| Emails not detected | Smart Filter too strict for this email | Check execution log; add keywords if needed |
| Wrong product detected | Keyword ambiguity | Review Parse Email node output; adjust patterns |
| Measurements not parsed | Unusual format | Check Parse Email output; add regex patterns |
| API call failing | API URL wrong or API down | Check Config node URL; verify `GET /health` returns ok |
| No draft appearing | Gmail credential lacks draft permission | Re-authorize with full Gmail scope |
| Sheet logging fails | Wrong Sheet ID or credential | Verify sheetId in Config; check Sheets credential |
| Reply loop detected | Auto-reply triggers on its own replies | Reply Chain Check should catch this; verify signatures |

## Files in This Directory

| File | Purpose |
|---|---|
| `sizing-email-workflow.json` | The importable n8n workflow (v2) |
| `email-template.html` | Reference HTML template for the sizing reply email |
| `README.md` | This file |
| `RENOVATION-PROMPT.md` | The prompt used to generate the v2 renovation |
