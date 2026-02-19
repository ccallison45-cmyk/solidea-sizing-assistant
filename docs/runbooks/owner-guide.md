# Owner Guide: Solidea Sizing Assistant

This guide is for the store owner. It covers the day-to-day operations you may need to perform without developer help.

---

## How the System Works

```
Customer on solideaus.com          Customer emails sizing question
        |                                    |
  [Sizing Widget]                    [n8n Email Workflow]
        |                                    |
        +----------> Sizing API <------------+
                   (Railway/Render)
                         |
                   data/*.json
                 (sizing charts)
```

1. **Widget**: A "Find My Size" button appears on product pages. Customers enter their measurements and get an instant size recommendation.
2. **Email**: When a customer emails a sizing question, n8n automatically parses the measurements, calls the same API, and sends a reply. If it can't parse the email, it forwards it to you.
3. **API**: The backend reads sizing charts from JSON files and matches measurements to sizes.

---

## Updating Sizing Data

If Solidea changes a size chart, you need to update the corresponding JSON file and redeploy.

### Step 1: Find the right file

| Product | File |
|---|---|
| Arm Sleeves | `data/arm-sleeves.json` |
| Leggings | `data/leggings.json` |
| Capris | `data/capris.json` |
| Knee-High Socks | `data/socks.json` |
| Bras | `data/bras.json` |

### Step 2: Edit the file

Each file is a list of sizes. Each size has measurement ranges with `min` and `max` values.

**Example** (from `data/socks.json`):

```json
[
  {
    "size": "S",
    "measurements": {
      "calf_circumference_cm": { "min": 29, "max": 34 },
      "ankle_circumference_cm": { "min": 19, "max": 21 }
    }
  },
  {
    "size": "M",
    "measurements": {
      "calf_circumference_cm": { "min": 32, "max": 37 },
      "ankle_circumference_cm": { "min": 20, "max": 22 }
    }
  }
]
```

**To change a range**, edit the `min` or `max` number. For example, if the S calf range changes to 28-35:

```json
"calf_circumference_cm": { "min": 28, "max": 35 }
```

**To add a new size**, copy an existing entry, change the `"size"` label, and update the measurement ranges.

**Rules**:
- `min` must be less than or equal to `max`
- All measurements must be in **centimeters** (or kilograms for weight)
- Every size must have at least one measurement
- Don't delete the square brackets `[ ]` at the start and end of the file

### Step 3: Save and deploy

1. Save the file
2. Commit and push to the `main` branch on GitHub
3. The API will automatically redeploy (takes 1-2 minutes)
4. Test by using the widget on your store to verify the new data

### Validating your edit

If you have Python and uv installed locally, you can check your edit before deploying:

```bash
uv run pytest tests/test_sizing_logic.py -v
```

If the tests pass, your JSON files are valid. If you get an error about "invalid JSON" or "min > max", check the file you edited for typos.

---

## Checking the n8n Email Workflow

### Is it running?

1. Log into your n8n instance
2. Go to **Workflows** and find "Solidea Sizing Email Assistant"
3. The toggle should be **green** (active)
4. Click the workflow to see the execution history

### Recent executions

In the workflow editor, click **Executions** in the left sidebar. You'll see a list of recent runs. Each shows:
- **Success** (green): Email was processed and a reply was sent
- **Error** (red): Something went wrong — click to see details

### Common problems

| Problem | What to check |
|---|---|
| Workflow not triggering | Is the toggle active? Are IMAP credentials still valid? |
| Emails not being detected | Check the "Is Sizing Inquiry?" filter — the subject/body might not contain expected keywords |
| API call failing | Is the API still running? Check the health endpoint URL |
| Reply not sending | Check SMTP credentials — password may have expired |

### Testing the workflow manually

Send a test email to your inbox:

```
Subject: What size leggings should I get?
Body: I'm 170cm tall and weigh 65kg. My waist is 70cm and hips are 93cm.
```

Within 5 minutes, you should receive an auto-reply with a size recommendation.

---

## Reading API Logs

### On Render

1. Go to https://dashboard.render.com
2. Click your service ("solidea-sizing-api")
3. Click **Logs** in the left sidebar
4. You'll see real-time log output

### On Railway

1. Go to https://railway.com/dashboard
2. Click your project
3. Click the service
4. Click **Logs** tab

### What to look for

- `Sizing data loaded: ['arm_sleeves', 'leggings', 'capris', 'socks', 'bras']` — healthy startup
- `Loading sizing data from data` — app is starting up
- HTTP request logs show incoming API calls
- Any `ERROR` lines indicate a problem

---

## Keeping the API Warm (Preventing Cold Starts)

Free-tier hosting platforms put your app to sleep after ~15 minutes of inactivity. The first request after sleep takes 5-30 seconds.

### Option A: UptimeRobot (recommended, free)

1. Go to https://uptimerobot.com and create a free account
2. Click **Add New Monitor**
3. Set:
   - Monitor Type: **HTTP(s)**
   - Friendly Name: `Solidea Sizing API`
   - URL: `https://YOUR-API-URL/health`
   - Monitoring Interval: **5 minutes**
4. Save — UptimeRobot will ping your API every 5 minutes to keep it awake

### Option B: cron-job.org (free alternative)

1. Go to https://cron-job.org and create a free account
2. Create a new cron job
3. URL: `https://YOUR-API-URL/health`
4. Schedule: every 5 minutes
5. Save and enable

---

## Quick Health Check

Run this from any browser or terminal to verify the API is up:

```
https://YOUR-API-URL/health
```

Expected response: `{"status": "ok"}`

If you get an error or timeout, the API may be down. Check the hosting platform dashboard for deployment status or errors.

---

## Contact for Technical Issues

If something is broken and you can't fix it with this guide:

1. Check the API health endpoint first
2. Check the n8n execution history for errors
3. Check the hosting platform (Render/Railway) logs
4. If none of that helps, contact the developer with:
   - What's not working (widget? email? both?)
   - Any error messages you see
   - When it last worked correctly
