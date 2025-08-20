# Deployment Guide: GitHub-Native Backend

This guide shows how to deploy the hybrid architecture that preserves your excellent UX while enabling automated backend processing.

## Architecture Overview

```
User adds site → Serverless function → GitHub issue → GitHub Actions → Site added
              ↓
          Immediate UX feedback (site appears as "Processing")
```

## Setup Steps

### 1. Deploy Serverless Function (Vercel - Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy from project root
vercel --prod

# Set environment variables in Vercel dashboard
```

**Required Environment Variables in Vercel:**
- `GITHUB_TOKEN`: Personal access token with repo permissions
- `GITHUB_OWNER`: `ND-AAD`
- `GITHUB_REPO`: `Gov_Oversight`

### 2. GitHub Repository Settings

**Enable GitHub Actions:**
- Go to Settings → Actions → General
- Allow all actions and reusable workflows

**Set Repository Secrets:**
- `GITHUB_TOKEN`: Same token as Vercel (for workflow permissions)

**Enable Issues:**
- Go to Settings → General → Features
- Ensure "Issues" is checked

### 3. Frontend Configuration

Update your frontend environment variables:

```bash
# .env.local (for local development)
VITE_SERVERLESS_ENDPOINT=https://your-app.vercel.app/api/add-site
VITE_API_MODE=static
```

### 4. Test the Flow

1. **Add a test site** through the dashboard
2. **Check Vercel logs** to see function execution
3. **Check GitHub issues** for the created issue
4. **Check GitHub Actions** for processing workflow
5. **Verify site appears** in data/sites.json

## User Experience Flow

### Before (Broken)
```
User adds site → localStorage only → Nothing happens → User confused
```

### After (Working)
```
User adds site → [30s] "Processing" → [2m] "Testing" → [1m] "Active ✅ - Found 5 RFPs"
```

## Troubleshooting

### Serverless Function Issues
```bash
# Check Vercel function logs
vercel logs --follow

# Test function locally
vercel dev
curl -X POST http://localhost:3000/api/add-site -H "Content-Type: application/json" -d '{"name":"Test","base_url":"https://example.com"}'
```

### GitHub Actions Issues
- Check Actions tab for workflow runs
- Verify repository permissions for GITHUB_TOKEN
- Check issue labels (must include 'site-addition')

### Frontend Issues
- Check browser console for API errors
- Verify VITE_SERVERLESS_ENDPOINT is correct
- Test with browser dev tools Network tab

## Environment Variables Summary

**Vercel Environment Variables:**
```
GITHUB_TOKEN=github_pat_xxxxxxxxxxxxx
GITHUB_OWNER=ND-AAD  
GITHUB_REPO=Gov_Oversight
```

**Frontend Environment Variables:**
```
VITE_SERVERLESS_ENDPOINT=https://your-app.vercel.app/api/add-site
VITE_API_MODE=static
VITE_STATIC_DATA_BASE=/Gov_Oversight/data
```

## GitHub Token Permissions

Your GitHub token needs these permissions:
- `repo` (full repository access)
- `workflow` (if you want manual trigger capability)

## Alternative Serverless Providers

### Netlify Functions
```javascript
// netlify/functions/add-site.js
exports.handler = async (event, context) => {
  // Same logic as api/add-site.js
};
```

### Railway/Railway Functions
- Upload the same code structure
- Set same environment variables

## Security Considerations

- GitHub token is stored securely in Vercel environment
- No secrets exposed to frontend
- All GitHub API calls happen server-side
- Full audit trail through GitHub issues

## Monitoring

- **Vercel Dashboard**: Function execution metrics
- **GitHub Actions**: Processing workflow status  
- **GitHub Issues**: Full audit trail of site additions
- **Browser Console**: Frontend error reporting

---

This setup preserves your excellent UX while enabling scalable, transparent backend processing. Users see immediate feedback while the system processes requests reliably in the background.
