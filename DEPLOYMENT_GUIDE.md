# Deployment Guide: GitHub-Only Architecture

This guide shows how to deploy the simplified GitHub-only architecture that eliminates external dependencies while preserving excellent UX.

## Architecture Overview

```
User adds site → localStorage → GitHub Actions → Site added
              ↓
          Immediate UX feedback (site appears as "Processing")
```

## Setup Steps

### 1. GitHub Repository Configuration

**Enable GitHub Actions:**
- Go to Settings → Actions → General
- Allow all actions and reusable workflows

**Enable GitHub Pages:**
- Go to Settings → Pages
- Source: Deploy from a branch
- Branch: main / (root)

**Set Repository Secrets (if needed):**
- GitHub Actions use `GITHUB_TOKEN` automatically (no setup required)

### 2. Frontend Configuration (Optional)

For local development, you can set environment variables:

```bash
# .env.local (for local development only)
VITE_API_MODE=development  # Enables API server mode
```

### 3. Test the Flow

1. **Add a test site** through the dashboard
2. **Check browser localStorage** to see queued requests
3. **Check GitHub Actions** for processing workflow (runs hourly)
4. **Verify site appears** in data/sites.json after processing

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

### GitHub Actions Issues
- Check Actions tab for workflow runs
- Verify workflows are enabled in repository settings
- Check workflow files syntax in `.github/workflows/`

### Frontend Issues
- Check browser console for errors
- Verify localStorage for queued requests
- Check Network tab for failed static file requests

### Data Issues
- Ensure `data/` directory has proper JSON structure
- Check file permissions for GitHub Actions

## Environment Variables Summary

**GitHub Actions (automatic):**
```
GITHUB_TOKEN - Automatically provided
GITHUB_REPOSITORY - Automatically provided
```

**Frontend (optional for development):**
```
VITE_API_MODE=development    # For local API server
VITE_STATIC_DATA_BASE=/Gov_Oversight/data  # GitHub Pages path
```

## No External Dependencies

This architecture requires:
- ✅ GitHub repository (free)
- ✅ GitHub Pages (free)
- ✅ GitHub Actions (free for public repos)
- ❌ No Vercel account needed
- ❌ No API keys to manage
- ❌ No external services

## Security Considerations

- All processing happens within GitHub ecosystem
- No external API keys or tokens needed
- Full transparency through git history
- localStorage data stays in user's browser

## Monitoring

- **GitHub Actions**: Processing workflow status in Actions tab
- **GitHub Pages**: Site deployment status in repository settings
- **Browser Console**: Frontend error reporting and localStorage inspection
- **Git History**: Complete audit trail of all changes

---

This setup preserves your excellent UX while enabling scalable, transparent backend processing. Users see immediate feedback while the system processes requests reliably in the background.
