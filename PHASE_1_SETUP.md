# Phase 1: Environment Configuration

## Overview
Set up credentials and basic configuration for the whatsapp-agentkit project.

## Prerequisites
- Node.js 18+ installed
- An Anthropic API key (from console.anthropic.com)
- WhatsApp Business Account with provider credentials

## Step-by-Step Setup

### 1. Create Environment File
```bash
cp .env.example .env
```

### 2. Configure Claude API Key
1. Go to [https://console.anthropic.com](https://console.anthropic.com)
2. Create API key if you haven't already
3. Copy the key (starts with `sk-ant-`)
4. Update `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
   ```

### 3. Configure WhatsApp Credentials
1. Obtain WhatsApp phone number for your bot
2. Obtain authentication token from your WhatsApp provider (Whapi, etc.)
3. Update `.env`:
   ```
   WHATSAPP_PHONE_NUMBER=your-phone-with-country-code
   WHATSAPP_AUTH_TOKEN=your-auth-token
   ```

### 4. Configure Server
1. Set the port (default 3000):
   ```
   PORT=3000
   ```
2. Set environment:
   ```
   NODE_ENV=development
   ```

### 5. Configure Logging (Optional)
Set debug logging for development:
```
DEBUG=agentkit:*
LOG_LEVEL=debug
```

## Validation

Run the configuration validator to ensure all required variables are set:

```bash
node config-validator.js
```

You should see:
```
🔍 Validating whatsapp-agentkit configuration...

  ✅ ANTHROPIC_API_KEY: configured
  ✅ WHATSAPP_PHONE_NUMBER: configured
  ✅ PORT: configured

==================================================

✅ Configuration validation PASSED

✅ Ready to proceed to Phase 2: Project Structure Setup
Run: npm run setup
```

## Troubleshooting

### ❌ "ANTHROPIC_API_KEY: Claude API key from https://console.anthropic.com"
- You haven't set the API key or it still contains "sk-ant-" placeholder
- Go to https://console.anthropic.com and create a new key
- Copy the full key to your `.env` file

### ❌ "WHATSAPP_PHONE_NUMBER: Bot WhatsApp phone number"
- You haven't set the WhatsApp phone number
- Format: country code + number (e.g., 34123456789 for Spain)
- Don't include spaces or special characters

### ❌ ".env file not found"
- Run `cp .env.example .env` first

## Summary

✅ Phase 1 is complete when:
- `.env` file exists with all required variables
- `node config-validator.js` returns "Configuration validation PASSED"
- You're ready to proceed to Phase 2

## Next Steps

Once validation passes, proceed to **Phase 2: Project Structure Setup**:
```bash
npm run setup
```

This will initialize the project directory structure and create base files.
