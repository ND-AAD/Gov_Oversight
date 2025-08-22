# Vercel Deployment Guide

This guide walks through deploying the LA 2028 RFP Monitor to Vercel for a unified user experience.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Your Gov_Oversight repository
3. **GitHub Personal Access Token**: For GitHub API access

## Step 1: Create GitHub Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Set expiration to "No expiration" (or your preferred duration)
4. Select these scopes:
   - `repo` (Full control of private repositories)
   - `public_repo` (Access public repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again)

## Step 2: Deploy to Vercel

### Option A: Vercel CLI (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from project root
vercel

# Follow prompts:
# - Set up and deploy "~/Gov_Oversight"? [Y/n] y
# - Which scope? [your-username]
# - Link to existing project? [y/N] n
# - What's your project's name? gov-oversight
# - In which directory is your code located? ./
```

### Option B: Vercel Dashboard
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (project root)
   - **Build Command**: `npm run vercel-build`
   - **Output Directory**: `frontend/dist`

## Step 3: Configure Environment Variables

In Vercel Dashboard → Project → Settings → Environment Variables:

| Variable | Value | Environment |
|----------|--------|-------------|
| `GITHUB_TOKEN` | `github_pat_your_token_here` | Production, Preview, Development |
| `GITHUB_REPOSITORY` | `your-username/Gov_Oversight` | Production, Preview, Development |

**Important**: 
- Replace `your-username` with your actual GitHub username
- Replace `github_pat_your_token_here` with your actual token

## Step 4: Configure Custom Domain (Optional)

1. In Vercel Dashboard → Project → Settings → Domains
2. Add your custom domain (e.g., `rfp-monitor.yourdomain.com`)
3. Update DNS records as instructed by Vercel

## Step 5: Test the Deployment

1. Visit your Vercel URL (e.g., `https://gov-oversight.vercel.app`)
2. Try adding a test site:
   - Name: "Test Site" 
   - Base URL: "https://example.gov"
   - Main RFP Page: "https://example.gov/rfps"
3. Verify the GitHub issue is created automatically
4. Check that RFP data loads correctly

## Architecture Overview

```
User Browser → Vercel (Frontend + API) → GitHub API → GitHub Repository
                     ↓
              Serverless Functions
              - /api/add-site
              - /api/rfps  
              - /api/sites
              - /api/stats
```

## Benefits of Vercel Architecture

✅ **Seamless UX**: No GitHub account required for users
✅ **Unified Hosting**: Frontend and API in one place  
✅ **Auto-scaling**: Serverless functions scale automatically
✅ **Fast Global CDN**: Sub-100ms response times worldwide
✅ **Zero Configuration**: Deploy with one command
✅ **Maintains Transparency**: Still creates public GitHub issues

## Migration from GitHub Pages

1. **Keep GitHub Actions**: Backend scraping workflows remain unchanged
2. **Update Repository Settings**: Disable GitHub Pages in repository settings
3. **Update Documentation**: Point users to new Vercel URL
4. **DNS Migration**: Update any custom domain DNS to point to Vercel

## Troubleshooting

### Error: "GitHub API error: 401 Unauthorized"
- Check your GitHub token has correct permissions
- Verify token isn't expired
- Ensure `GITHUB_REPOSITORY` format is correct

### Error: "Resource not found" when loading data
- Verify your repository has `data/rfps.json` and `data/sites.json` files
- Check repository is public or token has private repo access

### Build fails with "vercel-build script not found"
- Run `npm install` in the project root
- Verify `package.json` has the `vercel-build` script

### Site addition creates GitHub issue but data doesn't update
- GitHub Actions may take 5-10 minutes to process
- Check GitHub Actions tab for workflow status
- Verify the issue has the `site-addition` label

## Performance Optimization

- **Edge Functions**: API responses cached at edge locations
- **Static Assets**: Frontend files served from global CDN
- **Function Duration**: API calls complete in <5 seconds
- **Cold Starts**: Minimal due to Vercel's serverless architecture

## Security

- **Environment Variables**: Securely stored in Vercel
- **GitHub Token**: Never exposed to client-side code
- **CORS**: Properly configured for cross-origin requests
- **Rate Limiting**: Built into Vercel functions

## Cost Estimate

Vercel pricing for this project:
- **Hobby Plan**: Free tier covers up to 100 GB bandwidth
- **Pro Plan**: $20/month if you exceed free limits
- **Estimated Usage**: ~1-5 GB/month for typical activist use

Most deployments will stay within the free tier.

---

## Next Steps After Deployment

1. **Test Site Addition**: Verify end-to-end workflow
2. **Update Documentation**: Point users to new Vercel URL
3. **Monitor Usage**: Check Vercel analytics dashboard
4. **Set Up Alerts**: Configure monitoring for uptime

Your LA 2028 RFP Monitor is now deployed with a unified, user-friendly architecture! 🎉