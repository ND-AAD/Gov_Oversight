# Setup Guide: Permissions & Connections First

## Step 1: Create GitHub Personal Access Token

1. **Go to GitHub Settings**:
   - GitHub.com → Your Profile → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **Generate New Token**:
   - Click "Generate new token (classic)"
   - **Name**: `LA-2028-RFP-Monitor-Vercel`
   - **Expiration**: `No expiration` (or 1 year)

3. **Required Permissions** (check these boxes):
   ```
   ✅ repo (Full control of private repositories)
     ✅ repo:status (Access commit status)
     ✅ repo_deployment (Access deployment status) 
     ✅ public_repo (Access public repositories)
     ✅ repo:invite (Access repository invitations)
   
   ✅ workflow (Update GitHub Action workflows)
   
   ✅ write:packages (Write packages to GitHub Package Registry)
   ✅ read:packages (Read packages from GitHub Package Registry)
   ```

4. **Copy the Token**: 
   - Click "Generate token"
   - **⚠️ COPY IT IMMEDIATELY** - you won't see it again
   - Save it somewhere secure temporarily

## Step 2: Test GitHub Token Locally

Before deploying, let's verify the token works:

```bash
# Test the token (replace YOUR_TOKEN_HERE with actual token)
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/repos/YOUR_USERNAME/Gov_Oversight

# You should see JSON with repository information
# If you get 404 or 401, the token needs more permissions
```

## Step 3: Connect Vercel to GitHub

### Option A: Vercel CLI (Recommended)
```bash
# Install Vercel CLI if not already installed
npm i -g vercel

# Login to Vercel
vercel login

# Link your GitHub repository
vercel link
# Follow prompts:
# - Set up and deploy? Y
# - Which scope? [your-username]
# - Link to existing project? N
# - Project name: gov-oversight
# - Directory: ./ 
```

### Option B: Vercel Dashboard
1. Go to [vercel.com/new](https://vercel.com/new)
2. Click "Import Git Repository"
3. Select your `Gov_Oversight` repository
4. **Don't deploy yet** - just import

## Step 4: Configure Environment Variables in Vercel

### Via Vercel Dashboard:
1. Go to your project → Settings → Environment Variables
2. Add these variables for **Production**, **Preview**, **Development**:

| Variable Name | Value | Environment |
|---------------|--------|-------------|
| `GITHUB_TOKEN` | `github_pat_your_token_here` | All |
| `GITHUB_REPOSITORY` | `your-username/Gov_Oversight` | All |

### Via Vercel CLI:
```bash
# Set environment variables
vercel env add GITHUB_TOKEN
# Paste your token when prompted
# Select: Production, Preview, Development

vercel env add GITHUB_REPOSITORY  
# Enter: your-username/Gov_Oversight
# Select: Production, Preview, Development
```

## Step 5: Test Connections Before Deployment

Let's create a simple test to verify everything works:

### Create Test API Endpoint
Create `/api/test-connection.ts`:
```typescript
import { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const githubToken = process.env.GITHUB_TOKEN;
  const githubRepo = process.env.GITHUB_REPOSITORY;
  
  if (!githubToken || !githubRepo) {
    return res.status(500).json({ 
      error: 'Missing environment variables',
      has_token: !!githubToken,
      has_repo: !!githubRepo
    });
  }

  try {
    // Test GitHub API connection
    const response = await fetch(`https://api.github.com/repos/${githubRepo}`, {
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'LA-2028-RFP-Monitor-Test/1.0'
      }
    });

    if (!response.ok) {
      return res.status(response.status).json({
        error: 'GitHub API test failed',
        status: response.status,
        statusText: response.statusText
      });
    }

    const repoData = await response.json();
    
    return res.status(200).json({
      success: true,
      message: 'All connections working!',
      repository: {
        name: repoData.full_name,
        private: repoData.private,
        permissions: repoData.permissions
      },
      environment_check: {
        has_github_token: true,
        has_github_repo: true,
        vercel_function: true
      }
    });

  } catch (error) {
    return res.status(500).json({
      error: 'Connection test failed',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
```

### Test Deployment
```bash
# Deploy just the test endpoint
vercel --prod

# Test the connection
curl https://your-project.vercel.app/api/test-connection

# You should see:
# {
#   "success": true,
#   "message": "All connections working!",
#   "repository": { ... },
#   "environment_check": { ... }
# }
```

## Step 6: Verify GitHub Workflow Permissions

Your GitHub repository needs to allow workflows to be triggered via API:

1. **Repository Settings**:
   - Go to your GitHub repository
   - Settings → Actions → General

2. **Workflow Permissions**:
   - Ensure "Allow GitHub Actions to create and approve pull requests" is **enabled**
   - Set "Workflow permissions" to **Read and write permissions**

3. **Actions Permissions**:
   - Set to "Allow all actions and reusable workflows"

## Step 7: Test Complete Flow

Once connections are verified, test the complete flow:

### Test Site Addition
```bash
# Test adding a site via API
curl -X POST https://your-project.vercel.app/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Site", 
    "base_url": "https://example.gov",
    "main_rfp_page_url": "https://example.gov/rfps"
  }'
```

### Expected Result:
1. ✅ API responds in ~2 seconds
2. ✅ New commit appears in your GitHub repository
3. ✅ `data/sites.json` is updated
4. ✅ GitHub Actions workflow is triggered (optional)

## Troubleshooting Common Issues

### ❌ "401 Unauthorized"
- Token lacks required permissions
- Token has expired
- Repository name is incorrect

**Fix**: Regenerate token with correct permissions

### ❌ "403 Forbidden" 
- Token doesn't have write access to repository
- Repository settings block API access

**Fix**: Check repository permissions and workflow settings

### ❌ "404 Not Found"
- Repository name is wrong in GITHUB_REPOSITORY
- Repository is private but token lacks private repo access

**Fix**: Verify repository name format: `username/repository`

### ❌ Environment variables not found
- Variables not set in Vercel
- Variables set for wrong environment (prod vs preview vs dev)

**Fix**: Set variables for all environments in Vercel dashboard

## ✅ Verification Checklist

Before deploying the full API suite, ensure:

- [ ] GitHub token created with correct permissions
- [ ] Token tested locally and works
- [ ] Vercel project connected to GitHub repository
- [ ] Environment variables set in Vercel (all environments)
- [ ] Test API endpoint deployed and returns success
- [ ] GitHub repository workflow permissions configured
- [ ] Can successfully read repository via API
- [ ] Can successfully trigger workflows via API (if needed)

Once this checklist is complete, you're ready to deploy the full direct-update API suite! 🚀

## Next Steps

After verification is complete:
1. Deploy the full API suite from `DIRECT_API_ARCHITECTURE.md`
2. Update the frontend to use the new direct APIs
3. Test the complete user workflow
4. Celebrate your brittleness-free system! 🎉