# Phase 3: WhatsApp Integration

## Overview
Establish WhatsApp connection and message flow. Test communication between your bot and WhatsApp.

## Prerequisites
- Phase 1 & 2 completed
- `.env` configured with WhatsApp credentials
- Node.js dependencies installed (`npm install`)

## Step 1: Install Dependencies

```bash
npm install
```

This will install all required packages including:
- Express.js for the server
- Anthropic SDK for Claude integration
- Axios for HTTP requests
- TypeScript for type safety

## Step 2: Start Development Server

```bash
npm run dev
```

You should see:
```
✅ WhatsApp connection verified

╔════════════════════════════════════════╗
║  🚀 whatsapp-agentkit Server Ready    ║
╚════════════════════════════════════════╝

Server running on port 3000
📍 Webhook: http://localhost:3000/webhook
🏥 Health: http://localhost:3000/health
🤖 Agent: http://localhost:3000/agent
🧪 Test: POST http://localhost:3000/test
```

## Step 3: Test Local Connection

### Option A: Test Echo Agent Locally
```bash
curl -X POST http://localhost:3000/test \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, Echo Agent!"}'
```

Expected response:
```json
{
  "request": "Hello, Echo Agent!",
  "response": "I received your message: Hello, Echo Agent!",
  "timestamp": "2026-05-26T12:00:00.000Z"
}
```

### Option B: Check Server Health
```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2026-05-26T12:00:00.000Z",
  "agent": {
    "name": "echo-agent",
    "description": "Echo agent for testing message flow",
    "tools": []
  }
}
```

## Step 4: Configure Webhook URL (For Production)

When you deploy to production, you need to configure your WhatsApp provider's webhook:

### For Whapi.io:
1. Log in to Whapi dashboard
2. Go to Webhook Settings
3. Set webhook URL: `https://your-domain.com/webhook`
4. Select events: "message" and "message_status"
5. Save and verify

### For Meta API:
1. Go to Meta App Dashboard
2. Settings → Webhooks
3. Set callback URL: `https://your-domain.com/webhook`
4. Set verify token: Save a random token
5. Subscribe to webhook fields: messages, message_status

## Step 5: Test WhatsApp Connection (When Deployed)

Once deployed:

1. **Send a message** from WhatsApp to your bot number
2. **Check server logs** to see incoming webhook
3. **Verify bot response** appears in WhatsApp

Example webhook format (Whapi):
```json
{
  "messages": [
    {
      "from": "573243939750",
      "to": "your-bot-number",
      "text": {
        "body": "Hello bot!"
      },
      "id": "wamid.xxx",
      "timestamp": 1234567890
    }
  ]
}
```

## File Structure Created

```
src/
├── transports/
│   └── WhatsAppTransport.ts      # WhatsApp API integration
├── agents/
│   ├── BaseAgent.ts              # Base agent class
│   └── EchoAgent.ts              # Echo agent for testing
└── index.ts                       # Main server file
```

## Key Components

### WhatsAppTransport
- `sendMessage(to, text)` - Send text message
- `sendMedia(to, url, type, caption)` - Send media
- `parseWebhookMessage(data)` - Parse incoming messages
- `checkConnection()` - Verify WhatsApp connection

### BaseAgent
- `handle(message)` - Process incoming message with Claude
- `resetConversation()` - Clear conversation history
- `getMetadata()` - Get agent info
- `getHistory()` - Get conversation history

### EchoAgent
- Simple agent for testing
- Repeats user messages
- Verifies message flow works

## Common Issues

### ❌ "WHATSAPP_AUTH_TOKEN is empty"
- Check `.env` file has token set
- Token should start with actual value, not "placeholder"

### ❌ "WhatsApp connection check failed"
- Token may be invalid or expired
- Check Whapi/Meta dashboard for token validity
- Connection check is optional; webhook might still work

### ❌ "Webhook receives messages but no response sent"
- Check server logs for agent errors
- Verify Claude API key is valid
- Check message format is correct for agent

### ❌ "ANTHROPIC_API_KEY error"
- Get API key from https://console.anthropic.com
- Make sure it starts with `sk-ant-`
- Update `.env` and restart server

## Testing Flow

```
Local Testing:
curl /test endpoint → EchoAgent → Response

Production Testing:
WhatsApp User → Whapi/Meta → /webhook → EchoAgent → Response → WhatsApp User
```

## Next Steps

Once Phase 3 is complete:

1. ✅ Server starts without errors
2. ✅ Health check returns 200
3. ✅ `/test` endpoint works locally
4. ✅ (When deployed) WhatsApp messages trigger webhook

Proceed to **Phase 4: Agent Development** to create custom agents.
