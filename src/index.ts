import express, { Request, Response } from 'express';
import dotenv from 'dotenv';
import WhatsAppTransport from './transports/WhatsAppTransport';
import EchoAgent from './agents/EchoAgent';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize WhatsApp Transport
const whatsapp = new WhatsAppTransport(
  process.env.WHATSAPP_AUTH_TOKEN || '',
  process.env.WHATSAPP_PHONE_NUMBER || ''
);

// Initialize agents
const echoAgent = new EchoAgent();

// Middleware
app.use(express.json());

// Webhook endpoint for incoming messages
app.post('/webhook', async (req: Request, res: Response) => {
  try {
    console.log('📨 Incoming webhook:', JSON.stringify(req.body, null, 2));

    // Parse message
    const message = whatsapp.parseWebhookMessage(req.body);

    if (!message || !message.text) {
      console.log('⚠️  No valid message found in webhook');
      return res.json({ success: true });
    }

    console.log(`📝 Message from ${message.from}: ${message.text}`);

    // Process message with agent
    const response = await echoAgent.handle(message.text);

    // Send response
    const sendResult = await whatsapp.sendMessage(message.from, response);

    if (sendResult.success) {
      console.log(`✅ Response sent to ${message.from}`);
    } else {
      console.error(`❌ Failed to send response: ${sendResult.error}`);
    }

    res.json({ success: true, messageId: sendResult.messageId });
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).json({ success: false, error: 'Processing error' });
  }
});

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    agent: echoAgent.getMetadata(),
  });
});

// Agent info endpoint
app.get('/agent', (req: Request, res: Response) => {
  res.json({
    agent: echoAgent.getMetadata(),
    conversationLength: echoAgent.getHistory().length,
  });
});

// Test endpoint
app.post('/test', async (req: Request, res: Response) => {
  try {
    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: 'No message provided' });
    }

    const response = await echoAgent.handle(message);

    res.json({
      request: message,
      response,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    res.status(500).json({ error: 'Processing error' });
  }
});

// Initialize and start server
async function start() {
  // Check WhatsApp connection
  const isConnected = await whatsapp.checkConnection();
  if (isConnected) {
    console.log('✅ WhatsApp connection verified');
  } else {
    console.warn(
      '⚠️  WhatsApp connection check failed (may still work via webhook)'
    );
  }

  // Start server
  app.listen(PORT, () => {
    console.log('\n╔════════════════════════════════════════╗');
    console.log('║  🚀 whatsapp-agentkit Server Ready    ║');
    console.log('╚════════════════════════════════════════╝\n');
    console.log(`Server running on port ${PORT}`);
    console.log(`📍 Webhook: http://localhost:${PORT}/webhook`);
    console.log(`🏥 Health: http://localhost:${PORT}/health`);
    console.log(`🤖 Agent: http://localhost:${PORT}/agent`);
    console.log(`🧪 Test: POST http://localhost:${PORT}/test`);
    console.log('\n');
  });
}

start().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});
