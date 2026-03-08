# Frontend Deployment Quick Start

This is a condensed guide for deploying the AI Accounting Copilot frontend. For detailed information, see [DEPLOYMENT.md](./DEPLOYMENT.md).

## Prerequisites

- AWS CLI installed and configured
- Node.js 18+ and npm installed
- AWS account with S3, CloudFront permissions

## Quick Deployment (3 Steps)

### 1. Setup Infrastructure (One-time)

```bash
cd frontend
./setup-infrastructure.sh
```

This creates:
- S3 bucket: `accounting-copilot-web-{account-id}`
- CloudFront distribution with proper caching
- Saves config to `deploy.env`

**Wait 15-20 minutes** for CloudFront distribution to deploy.

### 2. Configure Environment

```bash
# Copy example and edit with your values
cp .env.example .env
nano .env  # or use your preferred editor
```

Required values in `.env`:
```env
VITE_API_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod
VITE_COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
VITE_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
VITE_COGNITO_REGION=us-east-1
```

### 3. Deploy

```bash
# Load deployment configuration
source deploy.env

# Deploy the frontend
./deploy.sh
```

## Verify Deployment

1. Check the CloudFront URL (from setup output)
2. Test SPA routing by navigating to `/dashboard` and refreshing
3. Verify the app loads and can connect to the API

## Redeploy After Changes

```bash
cd frontend
source deploy.env
./deploy.sh
```

## Troubleshooting

### CloudFront shows old version
- Wait 5-10 minutes for cache invalidation
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

### Build fails
```bash
npm run type-check  # Check TypeScript errors
npm run lint        # Check linting errors
```

### SPA routing returns 404
- Verify CloudFront custom error responses are configured
- Check setup-infrastructure.sh completed successfully

## Cost Estimate

**AWS Free Tier (first 12 months):**
- S3: 5 GB storage, 20K GET, 2K PUT requests/month
- CloudFront: 1 TB transfer, 10M requests/month

**Beyond Free Tier:** ~$1/month for typical usage

## Architecture

```
User Browser
    ↓
CloudFront CDN (HTTPS)
    ↓
S3 Static Website
    ├── index.html (no-cache)
    └── assets/ (1-year cache)
```

## Key Files

- `setup-infrastructure.sh` - Creates AWS infrastructure
- `deploy.sh` - Builds and deploys the app
- `deploy.env` - Deployment configuration (generated)
- `.env` - Application configuration (you create)
- `DEPLOYMENT.md` - Detailed deployment guide

## Support

For detailed instructions, troubleshooting, and CI/CD setup, see [DEPLOYMENT.md](./DEPLOYMENT.md).
