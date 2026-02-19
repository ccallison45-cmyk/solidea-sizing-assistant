# n8n Email Automation Workflow

This directory contains the n8n workflow that auto-replies to sizing inquiry emails.

## Workflow Overview

```
[IMAP Trigger] → [Filter: Is Sizing Inquiry?] → [Code: Parse Email] → [IF: Can Process?]
                                                                          ├── YES → [HTTP: Call Sizing API] → [Code: Format Reply] → [SMTP: Send Auto-Reply]
                                                                          └── NO  → [SMTP: Forward to Owner for Manual Review]
```

## Setup Instructions

### Prerequisites

- An n8n instance (cloud or self-hosted)
- IMAP access to the Solidea inbox (info@solideaus.com)
- SMTP credentials for sending replies
- The Sizing API deployed and accessible

### Step 1: Import the Workflow

1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `sizing-email-workflow.json` from this directory
4. The workflow will be imported in inactive state

### Step 2: Configure Credentials

You need to set up two credentials in n8n:

**IMAP Credential** (for reading emails):
- Host: your IMAP server (e.g., `imap.gmail.com`)
- Port: 993
- User: `info@solideaus.com`
- Password: your email password or app password
- SSL: enabled

**SMTP Credential** (for sending replies):
- Host: your SMTP server (e.g., `smtp.gmail.com`)
- Port: 465 or 587
- User: `info@solideaus.com`
- Password: your email password or app password
- SSL: enabled

### Step 3: Update Placeholders

In the workflow, replace these values:

1. **`REPLACE_WITH_API_URL`** in the "Get Size Recommendation" node → your production API URL (e.g., `https://solidea-sizing.up.railway.app`)
2. **`REPLACE_WITH_IMAP_CREDENTIAL_ID`** → select your IMAP credential from the dropdown
3. **`REPLACE_WITH_SMTP_CREDENTIAL_ID`** → select your SMTP credential from the dropdown

### Step 4: Set the Email Template

1. Open the **"Send Auto-Reply"** node
2. Set the HTML body to the contents of `email-template.html`
3. The template uses n8n expression variables (`{{ $json.recommendedSize }}`, etc.) that are populated by the "Format Reply" node

### Step 5: Activate

1. Click **"Save"** in the workflow editor
2. Toggle the workflow to **Active**
3. The workflow will now check the inbox every 5 minutes

## How It Works

### Email Detection

The workflow filters for sizing inquiries by checking the subject and body for keywords like "size", "sizing", "measurement", "fit", "what size", "which size".

### Measurement Parsing

The Code node uses regex patterns to extract measurements from the email body. It looks for patterns like:
- "height: 170 cm" or "height 170cm"
- "bust: 95" or "bust 95 cm"
- "waist: 70cm"
- "calf: 35"

Supported measurement keywords: height, weight, hip(s), waist, bust, underbust/under-bust, upper arm/bicep, forearm, wrist, calf, ankle.

### Auto-Reply vs. Escalation

- **Can process**: Both product type AND at least one measurement were detected → calls the API and sends an auto-reply
- **Cannot process**: Missing product type or no measurements found → forwards to owner with a flag for manual review

## Test Emails

To test the workflow, send emails like these to the monitored inbox:

### Should auto-reply:
```
Subject: What size leggings should I get?
Body: I'm 170cm tall and weigh 65kg. My waist is 70cm and hips are 93cm.
```

```
Subject: Arm sleeve sizing help
Body: My upper arm is 33cm, forearm is 26cm, and wrist is 17cm.
```

```
Subject: Bra size question
Body: Bust: 95cm, underbust: 77cm
```

### Should forward to owner:
```
Subject: Sizing question
Body: What size should I get? I usually wear a medium in other brands.
```
(No measurements detected → forwarded)

```
Subject: Do you have size XL in blue?
Body: I want to order the blue ones in XL.
```
(Not really a sizing inquiry, but if it passes the filter, no measurements → forwarded)

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| Workflow not triggering | IMAP credentials wrong or inactive workflow | Check credentials; ensure workflow is toggled active |
| Emails not detected as sizing | Subject/body missing keywords | Check filter conditions; add more keywords if needed |
| Measurements not parsed | Unusual email format | Check the Parse Email node's output; adjust regex |
| API call failing | Wrong URL or API is down | Verify API URL; check API health endpoint |
| Reply not sending | SMTP credentials wrong | Test SMTP credentials in n8n credential editor |
