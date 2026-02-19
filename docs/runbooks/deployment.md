# Deployment Guide

## Overview

The Solidea Sizing API can be deployed to either **Render** or **Railway** (both offer free tiers). The project includes configuration for both platforms.

## Option A: Deploy to Render (recommended)

Render offers a free web service tier with auto-deploy from GitHub.

### Initial Setup

1. Push this repository to GitHub
2. Go to https://dashboard.render.com
3. Click **New** > **Web Service**
4. Connect your GitHub account and select this repository
5. Render will detect the `render.yaml` and auto-configure the service
6. Alternatively, configure manually:
   - **Build Command**: `pip install uv && uv sync --no-dev`
   - **Start Command**: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Environment Variables

Set these in Render's dashboard under **Environment**:

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `APP_LOG_LEVEL` | `info` |
| `ALLOWED_ORIGINS` | `https://solideaus.com,https://www.solideaus.com` |
| `SIZING_DATA_DIR` | `data` |

### Verify

After deployment completes (1-2 minutes), visit:

```
https://your-service.onrender.com/health
```

Expected: `{"status": "ok"}`

## Option B: Deploy to Railway

Railway auto-detects the Dockerfile.

### Initial Setup

1. Push this repository to GitHub
2. Go to https://railway.com
3. Click **New Project** > **Deploy from GitHub Repo**
4. Select this repository
5. Railway will detect `railway.json` and `Dockerfile`

### Environment Variables

Set these in Railway's dashboard under **Variables**:

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `APP_LOG_LEVEL` | `info` |
| `ALLOWED_ORIGINS` | `https://solideaus.com,https://www.solideaus.com` |
| `SIZING_DATA_DIR` | `data` |
| `PORT` | (Railway sets this automatically) |

### Verify

Railway provides a public URL after deployment. Visit:

```
https://your-project.up.railway.app/health
```

## After Deployment

### 1. Update the Shopify widget

Edit the Shopify theme to point the widget at your production API URL:

```html
<script>
  window.SolideaSizingConfig = {
    apiUrl: 'https://your-production-url.com'
  };
</script>
<script src="https://your-production-url.com/static/sizing-widget.js" defer></script>
```

See `widget/shopify-install.liquid` for the complete Liquid snippet.

### 2. Update the n8n workflow

In the n8n workflow, update the "Get Size Recommendation" node URL:

```
https://your-production-url.com/api/v1/size-recommendation
```

### 3. Set up keep-alive pinger

See the "Keeping the API Warm" section in `docs/runbooks/owner-guide.md`.

## Redeployment

Both Render and Railway auto-deploy when you push to the `main` branch on GitHub. Just:

```bash
git add .
git commit -m "your changes"
git push origin main
```

The deployment will start automatically within seconds.

## Monitoring

- **Render**: Dashboard > your service > Logs
- **Railway**: Dashboard > your project > your service > Logs
- **API Health**: `GET /health` returns `{"status": "ok"}`
- **API Docs**: `GET /docs` shows the interactive Swagger UI
