# WhatsApp Configuration Guide

## Overview
This guide explains how to set up WhatsApp credentials for the whatsapp-agentkit project. We support two approaches:

1. **Whapi.io** - Recommended for simplicity
2. **Meta WhatsApp Business API** - For enterprise scale

## Option 1: Whapi.io (Recommended - Simpler)

### Step 1: Create Whapi Account
1. Go to https://whapi.io
2. Sign up for a free account
3. Verify your email

### Step 2: Create WhatsApp Instance
1. Log in to Whapi dashboard
2. Click "Create Instance"
3. Scan QR code with your WhatsApp Business Account (or regular WhatsApp)
4. Wait for "Connected" status

### Step 3: Get Credentials
1. In Whapi dashboard, go to Settings
2. Find and copy:
   - **Token** (API key) → `WHATSAPP_AUTH_TOKEN`
   - **Phone Number** → `WHATSAPP_PHONE_NUMBER`

### Step 4: Configure Webhook
1. In Whapi dashboard → Webhook Settings
2. Set webhook URL:
   ```
   https://your-app-domain.com/webhook
   ```
   (You'll update this after deployment)
3. Select events: "message" and "message_status"
4. Save webhook

### Example Configuration
```env
WHATSAPP_PHONE_NUMBER=34123456789
WHATSAPP_AUTH_TOKEN=your_whapi_token_here
```

---

## Option 2: Meta WhatsApp Business API (Enterprise)

### Prerequisites
- Meta Business Account
- WhatsApp Business Account
- Business Phone Number
- Payment method configured

### Step 1: Create Meta App
1. Go to https://developers.facebook.com
2. Click "My Apps" → "Create App"
3. Choose "Business" as app type
4. Fill in app details

### Step 2: Configure WhatsApp Integration
1. In your app dashboard, find "WhatsApp"
2. Click "Set Up"
3. Enter your phone number
4. Verify ownership of phone number

### Step 3: Get Credentials
1. In WhatsApp Settings → API Setup
2. Copy:
   - **Phone Number ID** → `WHATSAPP_PHONE_NUMBER_ID`
   - **Business Account ID** → `WHATSAPP_BUSINESS_ACCOUNT_ID`
   - **Access Token** → `WHATSAPP_AUTH_TOKEN`

### Step 4: Configure Webhook
1. In Settings → Webhooks
2. Set callback URL:
   ```
   https://your-app-domain.com/webhook
   ```
3. Generate and save webhook verify token
4. Subscribe to webhook events: messages, message_status

### Example Configuration
```env
WHATSAPP_PHONE_NUMBER_ID=1234567890
WHATSAPP_BUSINESS_ACCOUNT_ID=9876543210
WHATSAPP_AUTH_TOKEN=your_meta_token_here
```

---

## Testing Your Configuration

### 1. Send Test Message (via Whapi)
```bash
curl -X POST https://api.whapi.io/messages/text \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "34123456789",
    "body": "Hello, WhatsApp!"
  }'
```

### 2. Verify Webhook (via Meta API)
```bash
curl -X POST https://graph.instagram.com/v18.0/YOUR_PHONE_ID/messages \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "34123456789",
    "type": "text",
    "text": {"body": "Hello, WhatsApp!"}
  }'
```

---

## Common Issues

### ❌ "Invalid Token"
- Copy token again from dashboard (don't include spaces)
- Verify token is active in Whapi/Meta dashboard
- If expired, regenerate token

### ❌ "Phone Number Not Verified"
- Ensure WhatsApp Business Account is verified
- Verify phone number in Meta Business Manager
- Wait 24 hours after verification

### ❌ "Webhook Not Receiving Messages"
- Check webhook URL is publicly accessible
- Verify webhook signing in your code
- Check firewall/security settings

### ❌ "Message Delivery Failed"
- Ensure recipient has WhatsApp account
- Check rate limits (Meta: 1000 messages/day for new accounts)
- Verify phone number format (with country code)

---

## Security Best Practices

1. **Never commit tokens to git**
   - Always use `.env` file
   - Add `.env` to `.gitignore`

2. **Rotate tokens regularly**
   - Set 30-day rotation reminder
   - Update in deployment platform

3. **Use environment variables**
   - Different tokens for dev/staging/production
   - Keep tokens in encrypted vaults

4. **Monitor API usage**
   - Set rate limit alerts
   - Check daily message volume
   - Track failed messages

---

## Next Steps

1. Choose Whapi.io or Meta API (Whapi recommended for simplicity)
2. Follow setup steps for your chosen provider
3. Copy credentials to `.env`
4. Run validation:
   ```bash
   node config-validator.js
   ```
5. Proceed to Phase 2 when validation passes
