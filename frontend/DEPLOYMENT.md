# Frontend Deployment Guide

This guide provides step-by-step instructions for deploying the AI Accounting Copilot frontend to AWS S3 and CloudFront.

## Prerequisites

- AWS CLI installed and configured with appropriate credentials
- Node.js 18+ and npm installed
- AWS account with permissions for S3, CloudFront, and ACM (optional for SSL)

## Architecture Overview

The frontend is deployed as a static website with the following architecture:

- **S3 Bucket**: Hosts the built React application files
- **CloudFront Distribution**: CDN for global content delivery with HTTPS
- **Custom Error Responses**: Configured for SPA routing (404 → /index.html)
- **Caching Strategy**: 
  - Static assets (JS, CSS, images): 1 year cache
  - index.html: No cache (always fetch latest)

## Deployment Steps

### Step 1: Infrastructure Setup

First, create the required AWS infrastructure (S3 bucket and CloudFront distribution).

#### Option A: Using the Setup Script (Recommended)

```bash
cd frontend
chmod +x setup-infrastructure.sh
./setup-infrastructure.sh
```

The script will:
- Create an S3 bucket with the naming pattern: `accounting-copilot-web-{account-id}`
- Configure the bucket for static website hosting
- Create a CloudFront distribution with proper caching rules
- Set up custom error responses for SPA routing
- Output the CloudFront distribution ID and URL

#### Option B: Manual Setup via AWS Console

**Create S3 Bucket:**

1. Go to AWS S3 Console
2. Click "Create bucket"
3. Bucket name: `accounting-copilot-web-{your-account-id}`
4. Region: `us-east-1` (or your preferred region)
5. Uncheck "Block all public access" (CloudFront will access it)
6. Enable "Static website hosting" in bucket properties
   - Index document: `index.html`
   - Error document: `index.html`
7. Add bucket policy (replace `{your-account-id}`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::accounting-copilot-web-{your-account-id}/*"
    }
  ]
}
```

**Create CloudFront Distribution:**

1. Go to AWS CloudFront Console
2. Click "Create Distribution"
3. Origin Settings:
   - Origin Domain: Select your S3 bucket website endpoint (not the bucket itself)
   - Origin Path: Leave empty
   - Name: `S3-accounting-copilot-web`
4. Default Cache Behavior:
   - Viewer Protocol Policy: "Redirect HTTP to HTTPS"
   - Allowed HTTP Methods: GET, HEAD, OPTIONS
   - Cache Policy: Create custom or use "CachingOptimized"
5. Distribution Settings:
   - Price Class: "Use Only North America and Europe" (or as needed)
   - Alternate Domain Names (CNAMEs): Add your custom domain if you have one
   - SSL Certificate: 
     - Default CloudFront Certificate (*.cloudfront.net), OR
     - Custom SSL Certificate (requires ACM certificate)
   - Default Root Object: `index.html`
6. Custom Error Responses:
   - Add error response for 404:
     - HTTP Error Code: 404
     - Customize Error Response: Yes
     - Response Page Path: `/index.html`
     - HTTP Response Code: 200
   - Add error response for 403:
     - HTTP Error Code: 403
     - Customize Error Response: Yes
     - Response Page Path: `/index.html`
     - HTTP Response Code: 200
7. Click "Create Distribution"
8. Note the Distribution ID and Domain Name

### Step 2: Configure Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
cp .env.example .env
```

Edit `.env` with your AWS resource values:

```env
VITE_API_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod
VITE_COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
VITE_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
VITE_COGNITO_REGION=us-east-1
```

**How to get these values:**

- **VITE_API_URL**: From API Gateway console → Your API → Stages → prod → Invoke URL
- **VITE_COGNITO_USER_POOL_ID**: From Cognito console → User Pools → Your pool → Pool Id
- **VITE_COGNITO_CLIENT_ID**: From Cognito console → User Pools → Your pool → App clients → Client ID
- **VITE_COGNITO_REGION**: AWS region where Cognito is deployed (e.g., us-east-1)

### Step 3: Set Deployment Environment Variables

Export the following environment variables for the deployment script:

```bash
export S3_BUCKET="accounting-copilot-web-{your-account-id}"
export CLOUDFRONT_DIST_ID="E1234567890ABC"  # From CloudFront console
export AWS_REGION="us-east-1"
```

Or create a `deploy.env` file:

```bash
S3_BUCKET=accounting-copilot-web-123456789012
CLOUDFRONT_DIST_ID=E1234567890ABC
AWS_REGION=us-east-1
```

Then source it before deployment:

```bash
source deploy.env
```

### Step 4: Deploy the Frontend

Run the deployment script:

```bash
cd frontend
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. Install npm dependencies
2. Run TypeScript type checking
3. Run ESLint
4. Build the production bundle
5. Upload files to S3 with appropriate cache headers
6. Invalidate CloudFront cache

**Expected Output:**

```
AI Accounting Copilot - Frontend Deployment
==============================================
Installing dependencies...
Running type check...
Running linter...
Building application...
Uploading to S3 bucket: accounting-copilot-web-123456789012
Uploading index.html with no-cache...
Invalidating CloudFront cache...
CloudFront invalidation created
Deployment completed successfully!
==============================================
Frontend URL: https://accounting-copilot-web-123456789012.s3-website-us-east-1.amazonaws.com
CloudFront URL: Check your CloudFront distribution
```

### Step 5: Verify Deployment

1. **Check S3 Bucket**: Verify files are uploaded
   ```bash
   aws s3 ls s3://accounting-copilot-web-{your-account-id}/
   ```

2. **Test CloudFront URL**: Open the CloudFront domain name in a browser
   ```
   https://d1234567890abc.cloudfront.net
   ```

3. **Test SPA Routing**: Navigate to a non-root route and refresh
   - Should load the app correctly (not 404)
   - Example: `https://your-cloudfront-url.cloudfront.net/dashboard`

4. **Check Cache Headers**: Use browser DevTools Network tab
   - Static assets (JS/CSS): Should have `max-age=31536000`
   - index.html: Should have `no-cache, no-store, must-revalidate`

## Caching Strategy

### Static Assets (JS, CSS, Images)
- **Cache-Control**: `public, max-age=31536000` (1 year)
- **Rationale**: Vite generates unique hashes for each build, so files can be cached indefinitely

### index.html
- **Cache-Control**: `no-cache, no-store, must-revalidate`
- **Rationale**: Always fetch the latest version to get updated asset references

### CloudFront Cache Invalidation
- Invalidates all paths (`/*`) after each deployment
- Ensures users get the latest version immediately
- Cost: First 1,000 invalidation paths per month are free

## SSL/TLS Configuration

### Option 1: CloudFront Default Certificate (Free)
- Provides HTTPS via `*.cloudfront.net` domain
- No additional configuration needed
- Suitable for development and testing

### Option 2: Custom Domain with ACM Certificate

1. **Request Certificate in ACM** (must be in us-east-1 for CloudFront):
   ```bash
   aws acm request-certificate \
     --domain-name accounting.yourdomain.com \
     --validation-method DNS \
     --region us-east-1
   ```

2. **Validate Certificate**: Add DNS records as instructed by ACM

3. **Update CloudFront Distribution**:
   - Add CNAME: `accounting.yourdomain.com`
   - Select your ACM certificate

4. **Update DNS**: Add CNAME record pointing to CloudFront domain

## Troubleshooting

### Build Fails

**Issue**: TypeScript errors or linting errors

**Solution**:
```bash
npm run type-check  # Check TypeScript errors
npm run lint        # Check linting errors
```

Fix reported errors before deploying.

### S3 Upload Fails

**Issue**: Access denied or bucket not found

**Solution**:
- Verify AWS credentials: `aws sts get-caller-identity`
- Check bucket name and region
- Verify IAM permissions for S3 operations

### CloudFront Shows Old Version

**Issue**: Changes not visible after deployment

**Solution**:
- Wait 5-10 minutes for invalidation to complete
- Check invalidation status:
  ```bash
  aws cloudfront get-invalidation \
    --distribution-id E1234567890ABC \
    --id I1234567890ABC
  ```
- Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
- Clear browser cache

### SPA Routing Returns 404

**Issue**: Direct navigation to routes shows 404

**Solution**:
- Verify CloudFront custom error responses are configured
- Both 403 and 404 should redirect to `/index.html` with 200 status
- Check CloudFront distribution settings

### CORS Errors

**Issue**: API requests fail with CORS errors

**Solution**:
- Verify API Gateway has CORS enabled
- Check `VITE_API_URL` in `.env` matches API Gateway URL
- Ensure API Gateway allows your CloudFront domain

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/deploy-frontend.yml`:

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Create .env file
        run: |
          echo "VITE_API_URL=${{ secrets.VITE_API_URL }}" >> .env
          echo "VITE_COGNITO_USER_POOL_ID=${{ secrets.VITE_COGNITO_USER_POOL_ID }}" >> .env
          echo "VITE_COGNITO_CLIENT_ID=${{ secrets.VITE_COGNITO_CLIENT_ID }}" >> .env
          echo "VITE_COGNITO_REGION=${{ secrets.VITE_COGNITO_REGION }}" >> .env
      
      - name: Deploy
        env:
          S3_BUCKET: ${{ secrets.S3_BUCKET }}
          CLOUDFRONT_DIST_ID: ${{ secrets.CLOUDFRONT_DIST_ID }}
          AWS_REGION: us-east-1
        run: ./deploy.sh
```

**Required GitHub Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `VITE_API_URL`
- `VITE_COGNITO_USER_POOL_ID`
- `VITE_COGNITO_CLIENT_ID`
- `VITE_COGNITO_REGION`
- `S3_BUCKET`
- `CLOUDFRONT_DIST_ID`

## Cost Considerations

### AWS Free Tier (First 12 Months)
- **S3**: 5 GB storage, 20,000 GET requests, 2,000 PUT requests/month
- **CloudFront**: 1 TB data transfer out, 10M HTTP/HTTPS requests/month
- **CloudFront Invalidations**: First 1,000 paths/month free

### Beyond Free Tier
- **S3 Storage**: ~$0.023/GB/month
- **S3 Requests**: $0.0004/1,000 GET, $0.005/1,000 PUT
- **CloudFront Data Transfer**: $0.085/GB (first 10 TB)
- **CloudFront Requests**: $0.0075/10,000 HTTPS requests
- **CloudFront Invalidations**: $0.005 per path after first 1,000

**Estimated Monthly Cost** (typical SME usage):
- Storage (100 MB): ~$0.002
- Data Transfer (10 GB): ~$0.85
- Requests (100K): ~$0.08
- **Total: ~$1/month**

## Security Best Practices

1. **Enable S3 Bucket Encryption**: Already configured in setup script
2. **Use HTTPS Only**: CloudFront redirects HTTP to HTTPS
3. **Restrict S3 Access**: Only CloudFront should access S3 (use OAI)
4. **Environment Variables**: Never commit `.env` to version control
5. **IAM Permissions**: Use least-privilege IAM policies for deployment
6. **CloudFront Security Headers**: Consider adding security headers via Lambda@Edge

## Monitoring

### CloudWatch Metrics

Monitor these CloudFront metrics:
- **Requests**: Total number of requests
- **BytesDownloaded**: Data transfer volume
- **4xxErrorRate**: Client errors (check for broken links)
- **5xxErrorRate**: Server errors (should be near zero for static site)

### CloudWatch Alarms

Create alarms for:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name frontend-5xx-errors \
  --alarm-description "Alert on 5xx errors" \
  --metric-name 5xxErrorRate \
  --namespace AWS/CloudFront \
  --statistic Average \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

## Rollback Procedure

If a deployment causes issues:

1. **Revert to Previous Build**:
   ```bash
   git checkout <previous-commit>
   cd frontend
   ./deploy.sh
   ```

2. **Or Restore from S3 Versioning** (if enabled):
   ```bash
   aws s3api list-object-versions \
     --bucket accounting-copilot-web-{account-id} \
     --prefix index.html
   
   aws s3api copy-object \
     --bucket accounting-copilot-web-{account-id} \
     --copy-source accounting-copilot-web-{account-id}/index.html?versionId=<version-id> \
     --key index.html
   ```

3. **Invalidate CloudFront Cache**:
   ```bash
   aws cloudfront create-invalidation \
     --distribution-id E1234567890ABC \
     --paths "/*"
   ```

## Additional Resources

- [AWS S3 Static Website Hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [AWS CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [Vite Build Documentation](https://vitejs.dev/guide/build.html)
- [React Router and SPAs](https://reactrouter.com/en/main/start/concepts#client-side-routing)
