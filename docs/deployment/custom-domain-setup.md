# Custom Domain Setup for Azure Static Web Apps

## Overview

This document outlines the process for setting up custom domains and SSL certificates for the Steve's Mom AI Chatbot Azure Static Web App.

## Prerequisites

- Azure Static Web App deployed and running
- Domain name registered with a DNS provider
- Access to DNS management for the domain

## Custom Domain Configuration

### 1. Add Custom Domain in Azure Portal

1. Navigate to your Static Web App in the Azure Portal
2. Go to **Settings** > **Custom domains**
3. Click **+ Add** to add a new custom domain
4. Enter your domain name (e.g., `stevesmom.cannasol.tech`)
5. Choose domain type:
   - **CNAME** for subdomains (recommended)
   - **TXT** for apex domains

### 2. DNS Configuration

#### For Subdomain (CNAME Record)
```dns
Type: CNAME
Name: stevesmom (or your subdomain)
Value: <your-static-web-app>.azurestaticapps.net
TTL: 3600
```

#### For Apex Domain (TXT Record)
```dns
Type: TXT
Name: @
Value: <verification-token-from-azure>
TTL: 3600

Type: ALIAS/ANAME (if supported) or A Record
Name: @
Value: <static-web-app-ip-address>
TTL: 3600
```

### 3. Domain Validation

1. After adding DNS records, return to Azure Portal
2. Click **Validate** next to your custom domain
3. Wait for validation to complete (may take up to 24 hours)
4. Once validated, the domain status will show as "Ready"

## SSL Certificate Management

### Automatic SSL (Recommended)

Azure Static Web Apps automatically provisions and manages SSL certificates for custom domains:

- **Free SSL certificates** from DigiCert
- **Automatic renewal** before expiration
- **TLS 1.2 minimum** security standard
- **HTTP to HTTPS redirect** enabled by default

### Manual SSL Certificate

If you need to use your own SSL certificate:

1. Go to **Settings** > **Custom domains**
2. Click on your domain name
3. Select **Bring your own certificate**
4. Upload your certificate files:
   - Certificate file (.crt or .pem)
   - Private key file (.key)
   - Certificate chain (if applicable)

## Environment-Specific Domains

### Development
- Default: `<app-name>-dev.azurestaticapps.net`
- Custom: `dev.stevesmom.cannasol.tech`

### Staging
- Default: `<app-name>-staging.azurestaticapps.net`
- Custom: `staging.stevesmom.cannasol.tech`

### Production
- Default: `<app-name>.azurestaticapps.net`
- Custom: `stevesmom.cannasol.tech`

## Security Headers

The following security headers are automatically configured:

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

## Monitoring and Troubleshooting

### Common Issues

1. **DNS Propagation Delays**
   - Wait up to 24-48 hours for global DNS propagation
   - Use `nslookup` or `dig` to verify DNS records

2. **Certificate Provisioning Failures**
   - Ensure domain validation is complete
   - Check that domain points to correct Static Web App
   - Verify no conflicting DNS records exist

3. **Mixed Content Warnings**
   - Ensure all resources load over HTTPS
   - Update API endpoints to use HTTPS
   - Check for hardcoded HTTP URLs

### Verification Commands

```bash
# Check DNS resolution
nslookup stevesmom.cannasol.tech

# Test SSL certificate
openssl s_client -connect stevesmom.cannasol.tech:443 -servername stevesmom.cannasol.tech

# Check HTTP headers
curl -I https://stevesmom.cannasol.tech
```

## Bicep Template Integration

Custom domains can be configured via Bicep templates:

```bicep
resource customDomain 'Microsoft.Web/staticSites/customDomains@2022-03-01' = {
  parent: staticWebApp
  name: 'stevesmom.cannasol.tech'
  properties: {
    validationMethod: 'cname-delegation'
  }
}
```

## Cost Considerations

- **Custom domains**: Free with Azure Static Web Apps
- **SSL certificates**: Free (automatically managed)
- **DNS hosting**: Varies by provider
- **Premium certificates**: Optional, additional cost

## Next Steps

1. Register desired domain name
2. Configure DNS records as outlined above
3. Add custom domain in Azure Portal
4. Validate domain ownership
5. Test SSL certificate and HTTPS redirect
6. Update application configuration with new domain
7. Monitor certificate expiration and renewal
