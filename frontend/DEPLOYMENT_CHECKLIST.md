# Frontend Deployment Checklist

Use this checklist to ensure a successful deployment of the AI Accounting Copilot frontend.

## Pre-Deployment Checklist

### Prerequisites
- [ ] AWS CLI installed and configured
- [ ] Node.js 18+ and npm installed
- [ ] AWS account with appropriate permissions (S3, CloudFront, IAM)
- [ ] API Gateway endpoint deployed and accessible
- [ ] Cognito User Pool created and configured

### Environment Setup
- [ ] `.env` file created from `.env.example`
- [ ] `VITE_API_URL` configured with API Gateway URL
- [ ] `VITE_COGNITO_USER_POOL_ID` configured
- [ ] `VITE_COGNITO_CLIENT_ID` configured
- [ ] `VITE_COGNITO_REGION` configured

### Code Quality
- [ ] All TypeScript errors resolved (`npm run type-check`)
- [ ] All linting errors resolved (`npm run lint`)
- [ ] Tests passing (`npm run test`)
- [ ] Code committed to version control

## First-Time Infrastructure Setup

### Option A: Bash Script (Recommended)
- [ ] Run `./setup-infrastructure.sh`
- [ ] Review output for S3 bucket name
- [ ] Note CloudFront Distribution ID
- [ ] Note CloudFront URL
- [ ] Verify `deploy.env` file created
- [ ] Wait 15-20 minutes for CloudFront distribution to deploy

### Option B: CloudFormation
- [ ] Run `./deploy-cloudformation.sh`
- [ ] Wait for stack creation to complete
- [ ] Verify stack outputs in AWS Console
- [ ] Verify `deploy.env` file created

### Option C: Manual Setup
- [ ] Create S3 bucket: `accounting-copilot-web-{account-id}`
- [ ] Enable static website hosting
- [ ] Configure bucket policy for public read
- [ ] Enable bucket encryption (AES-256)
- [ ] Create CloudFront distribution
- [ ] Configure custom error responses (404/403 → /index.html)
- [ ] Note Distribution ID
- [ ] Create `deploy.env` file manually

## Deployment Checklist

### Pre-Deployment
- [ ] Source deployment configuration: `source deploy.env`
- [ ] Verify environment variables are set:
  - [ ] `S3_BUCKET`
  - [ ] `CLOUDFRONT_DIST_ID`
  - [ ] `AWS_REGION`
- [ ] Verify `.env` file exists and is configured

### Deployment Execution
- [ ] Run `./deploy.sh`
- [ ] Verify dependencies installed successfully
- [ ] Verify type checking passed
- [ ] Verify linting passed
- [ ] Verify build completed successfully
- [ ] Verify files uploaded to S3
- [ ] Verify CloudFront invalidation created

### Post-Deployment Verification
- [ ] Wait 5-10 minutes for CloudFront cache invalidation
- [ ] Open CloudFront URL in browser
- [ ] Verify application loads
- [ ] Verify HTTPS is enforced (HTTP redirects)
- [ ] Test login functionality
- [ ] Navigate to each page:
  - [ ] Dashboard
  - [ ] Transactions
  - [ ] Document Upload
  - [ ] Financial Assistant
  - [ ] Audit Trail
  - [ ] Approvals
- [ ] Test SPA routing (refresh on non-root route)
- [ ] Verify API connectivity
- [ ] Check browser console for errors
- [ ] Test on different browsers (Chrome, Firefox, Safari, Edge)
- [ ] Test on mobile device

## Cache Verification

### Browser DevTools Network Tab
- [ ] Static assets (JS/CSS) have `max-age=31536000` header
- [ ] `index.html` has `no-cache, no-store, must-revalidate` header
- [ ] CloudFront headers present (`X-Cache`, `X-Amz-Cf-Id`)

### CloudFront Console
- [ ] Distribution status is "Deployed"
- [ ] Origin is S3 website endpoint
- [ ] Custom error responses configured
- [ ] HTTPS redirect enabled
- [ ] Compression enabled

## Security Verification

- [ ] HTTPS enforced (no HTTP access)
- [ ] S3 bucket encryption enabled
- [ ] Bucket policy allows only read access
- [ ] CloudFront uses TLS 1.2+
- [ ] No sensitive data in client-side code
- [ ] Environment variables not exposed in build

## Performance Verification

- [ ] Dashboard loads in < 3 seconds
- [ ] Page transitions are smooth
- [ ] Images and assets load quickly
- [ ] No console warnings or errors
- [ ] Lighthouse score > 90 (optional)

## Monitoring Setup (Optional)

- [ ] CloudWatch alarms configured for:
  - [ ] 5xx error rate
  - [ ] 4xx error rate
  - [ ] Request count
  - [ ] Data transfer
- [ ] CloudWatch dashboard created
- [ ] SNS notifications configured for alarms

## Documentation

- [ ] Deployment date recorded
- [ ] CloudFront URL documented
- [ ] S3 bucket name documented
- [ ] Distribution ID documented
- [ ] Any issues encountered documented
- [ ] Team notified of deployment

## Rollback Plan (If Issues Occur)

- [ ] Previous commit hash noted
- [ ] Rollback procedure documented
- [ ] Team aware of rollback process
- [ ] Backup of previous build available (optional)

## Post-Deployment Tasks

- [ ] Monitor CloudWatch metrics for 24 hours
- [ ] Check for user-reported issues
- [ ] Verify all features working as expected
- [ ] Update deployment log
- [ ] Close deployment ticket/task

## Troubleshooting Reference

If issues occur, refer to:
- `DEPLOYMENT.md` - Comprehensive troubleshooting guide
- `DEPLOYMENT_QUICKSTART.md` - Quick fixes
- AWS CloudWatch Logs
- Browser console errors
- Network tab in DevTools

## Common Issues Quick Reference

### Application doesn't load
- Check CloudFront distribution status
- Verify S3 bucket has files
- Check browser console for errors
- Verify `.env` configuration

### SPA routing returns 404
- Verify CloudFront custom error responses
- Check error response configuration (404/403 → /index.html)

### API calls fail
- Verify `VITE_API_URL` in `.env`
- Check API Gateway CORS configuration
- Verify Cognito configuration
- Check browser console for CORS errors

### Old version showing
- Wait for CloudFront invalidation (5-10 minutes)
- Hard refresh browser (Ctrl+Shift+R)
- Check CloudFront invalidation status
- Verify new files in S3 bucket

### Authentication fails
- Verify Cognito User Pool ID and Client ID
- Check Cognito region configuration
- Verify user exists in Cognito
- Check browser console for auth errors

## Success Criteria

Deployment is successful when:
- ✅ Application loads via CloudFront URL
- ✅ HTTPS is enforced
- ✅ All pages are accessible
- ✅ SPA routing works correctly
- ✅ Authentication works
- ✅ API calls succeed
- ✅ No console errors
- ✅ Caching headers are correct
- ✅ Performance meets requirements

## Sign-Off

- [ ] Deployment completed by: ________________
- [ ] Date: ________________
- [ ] Verified by: ________________
- [ ] Date: ________________

---

**Note**: Keep this checklist updated as the deployment process evolves.
