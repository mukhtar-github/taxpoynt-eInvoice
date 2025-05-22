# Vercel Frontend Deployment Guide

This guide provides instructions for deploying the TaxPoynt eInvoice frontend to Vercel.

## Prerequisites

- GitHub repository with your TaxPoynt eInvoice code
- Vercel account (sign up at [vercel.com](https://vercel.com))
- Railway backend deployment (or other backend hosting)

## Deployment Steps

### 1. Connect Your Repository

1. Log in to your Vercel account
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Select the repository and configure as follows:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)

### 2. Configure Environment Variables

Add the following environment variables from the `frontend/vercel.env.template` file:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `NEXT_PUBLIC_API_URL` | URL to your backend API | `https://taxpoynt-api.up.railway.app/api/v1` |
| `NEXT_PUBLIC_AUTH_DOMAIN` | Domain for authentication | `taxpoynt-einvoice.vercel.app` |
| `NEXT_PUBLIC_AUTH_STORAGE_PREFIX` | Prefix for local storage | `taxpoynt_einvoice` |
| `NEXT_PUBLIC_DEFAULT_THEME` | Default UI theme | `light` |
| `NEXT_PUBLIC_FIRS_API_SANDBOX_MODE` | Use FIRS sandbox by default | `true` |
| `NEXT_PUBLIC_DEFAULT_TIME_RANGE` | Default dashboard time range | `24h` |

> **Important**: Ensure `NEXT_PUBLIC_API_URL` points to your Railway backend deployment.

### 3. Set Up CORS on Backend

Make sure your Railway backend has the following environment variable:

```
ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app
```

Replace `your-vercel-domain` with your actual Vercel domain.

### 4. Deploy Your Project

1. Click "Deploy" to start the deployment process
2. Vercel will build and deploy your application
3. Once complete, Vercel will provide a deployment URL

### 5. Set Up Custom Domain (Optional)

1. Go to the "Domains" section in your Vercel project settings
2. Add your custom domain
3. Follow Vercel's instructions for DNS configuration

### 6. Verify Security Headers

The deployment includes the following security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`

You can verify these headers using:
- [Security Headers Scanner](https://securityheaders.com)
- Browser developer tools (Network tab)

### 7. Test Integration Features

After deployment, test the following key features:

1. **Odoo Integration Dashboard**
   - Verify connection status indicators work
   - Test UBL field mapping visualization
   - Check Odoo submission metrics

2. **FIRS API Testing**
   - Test sandbox mode connectivity
   - Verify submission status checks
   - Test batch submission features

3. **Submission Dashboard**
   - Verify metrics are loading correctly
   - Test time range filtering
   - Check API status indicators

## Troubleshooting

### API Connection Issues

If the frontend cannot connect to the backend API:

1. Verify `NEXT_PUBLIC_API_URL` is set correctly
2. Check that CORS is properly configured on the backend
3. Ensure the Railway backend is running

### Build Failures

If the build fails:

1. Check the build logs in Vercel
2. Verify all dependencies are properly installed
3. Make sure TypeScript types are correct

### Authentication Problems

If users cannot log in:

1. Verify `NEXT_PUBLIC_AUTH_DOMAIN` is set correctly
2. Check that the backend authentication endpoints are working
3. Clear browser cookies and local storage, then try again

## Automated Deployments

Vercel automatically deploys:
- When you push to the main branch
- When you create a pull request (creates a preview deployment)

## Monitoring

1. Use Vercel Analytics to monitor performance
2. Check Vercel logs for any errors
3. Set up alerts for deployment failures

---

For more information, refer to the [Vercel documentation](https://vercel.com/docs).
