# Phase 5: Testing & Deployment

## Overview
Prepare for production: run tests, verify quality, and deploy your whatsapp-agentkit to Railway or another platform.

## Prerequisites
- Phase 1-4 completed
- Custom agent created
- All code tested locally

## Step 1: Quality Checks

### Type Checking
```bash
npm run type-check
```

Ensure no TypeScript errors. Fix any type issues before proceeding.

### Linting
```bash
npm run lint
```

Check code style. Fix issues with:
```bash
npm run lint:fix
```

### Build
```bash
npm run build
```

Compile TypeScript to JavaScript. Should complete without errors.

## Step 2: Local Testing

### Start Development Server
```bash
npm run dev
```

### Run All Tests
```bash
npm test
```

### Run Tests in Watch Mode
```bash
npm run test:watch
```

### Generate Coverage Report
```bash
npm run test:coverage
```

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:3000/health

# Test agent
curl -X POST http://localhost:3000/test \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'

# Get agent info
curl http://localhost:3000/agent
```

## Step 3: Create Tests

Create `tests/agents/RealEstateAgent.test.ts`:

```typescript
import RealEstateAgent from '../../src/agents/RealEstateAgent';

describe('RealEstateAgent', () => {
  let agent: RealEstateAgent;

  beforeEach(() => {
    agent = new RealEstateAgent();
  });

  it('should respond to property questions', async () => {
    const response = await agent.handle(
      'What properties do you have available?'
    );
    expect(response).toBeTruthy();
    expect(response.length).toBeGreaterThan(0);
  });

  it('should maintain conversation history', async () => {
    await agent.handle('Hello');
    const history = agent.getHistory();
    expect(history.length).toBeGreaterThan(0);
  });

  it('should reset conversation history', async () => {
    await agent.handle('Test message');
    agent.resetConversation();
    const history = agent.getHistory();
    expect(history.length).toBe(0);
  });
});
```

## Step 4: Environment Setup for Production

Update `.env` for production:

```env
# Production settings
NODE_ENV=production
LOG_LEVEL=warn
DEBUG=

# Ensure all credentials are set
ANTHROPIC_API_KEY=sk-ant-your-actual-key
WHATSAPP_PHONE_NUMBER=573243939750
WHATSAPP_AUTH_TOKEN=CexXPwtP6HwVFAfWcC1cw8zBynwZo8Bp

# Production port (Railway assigns this)
PORT=3000
```

Create `.env.production` for production-specific variables:

```env
NODE_ENV=production
LOG_LEVEL=warn
```

## Step 5: Deploy to Railway

### Prerequisites
- Railway account (https://railway.app)
- Git repository initialized
- All files committed

### Option A: Deploy via Railway Dashboard

1. Go to https://railway.app
2. Click "New Project"
3. Choose "Deploy from GitHub"
4. Select your repository
5. Configure environment variables
6. Deploy

### Option B: Deploy via Railway CLI

Install Railway CLI:
```bash
npm install -g @railway/cli
```

Login and deploy:
```bash
railway login
railway init
railway up
```

### Step 5.1: Configure Environment Variables in Railway

In Railway dashboard:
1. Go to your project
2. Select Variables
3. Add production values:
   - `ANTHROPIC_API_KEY`
   - `WHATSAPP_PHONE_NUMBER`
   - `WHATSAPP_AUTH_TOKEN`
   - `NODE_ENV=production`

### Step 5.2: Configure Webhook URL

After deployment, Railway provides a URL like:
```
https://whatsapp-agentkit-production.up.railway.app
```

1. Configure webhook in Whapi/Meta:
   - URL: `https://your-railway-url/webhook`
2. Save webhook configuration

## Step 6: Monitor Deployment

### Check Logs
```bash
railway logs
```

Look for:
- ✅ "🚀 whatsapp-agentkit Server Ready"
- ✅ "✅ WhatsApp connection verified"

### Test Production Endpoint
```bash
curl https://your-railway-url/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "...",
  "agent": {...}
}
```

### Test via WhatsApp

1. Send message to bot on WhatsApp
2. Check Railway logs for webhook receipt
3. Verify bot responds within 30 seconds

## Step 7: Error Handling & Monitoring

### Monitor Error Logs
```bash
railway logs --tail
```

Common errors:
- `ANTHROPIC_API_KEY is undefined` → Set in Railway variables
- `Connection refused` → Check port configuration
- `Invalid token` → Verify WhatsApp credentials

### Set Up Alerts

1. Go to Railway project settings
2. Configure notifications for:
   - Deployment failures
   - High error rates
   - Memory/CPU spikes

### Production Logging

Add monitoring to `src/index.ts`:

```typescript
// Log all errors
app.use((err: any, req: any, res: any, next: any) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Server error' });
});

// Health check with metrics
app.get('/metrics', (req, res) => {
  res.json({
    uptime: process.uptime(),
    memoryUsage: process.memoryUsage(),
    environment: process.env.NODE_ENV,
  });
});
```

## Step 8: Scaling & Optimization

### For Higher Volume

1. **Database for conversation history**
   - Implement conversation persistence
   - Use PostgreSQL or MongoDB

2. **Message queuing**
   - Use Redis for reliability
   - Implement retry logic

3. **Agent pools**
   - Create multiple agent instances
   - Load balance across instances

### Performance Optimization

1. **Cache responses** for common questions
2. **Reduce token usage** with shorter system prompts
3. **Monitor API costs** in Anthropic dashboard
4. **Set rate limits** to prevent abuse

## Step 9: Security Checklist

Before production:

- [ ] API keys in environment variables only
- [ ] `.env` added to `.gitignore`
- [ ] No credentials in code or commits
- [ ] Webhook signature validation enabled
- [ ] Rate limiting implemented
- [ ] Error messages don't expose sensitive info
- [ ] HTTPS enabled (Railway provides this)
- [ ] Regular dependency updates

## Deployment Checklist

Before deploying to production:

- [ ] `npm run lint` passes
- [ ] `npm run type-check` passes
- [ ] `npm run build` succeeds
- [ ] `npm test` passes or skipped intentionally
- [ ] All `.env` variables configured
- [ ] Webhook URL configured in Whapi/Meta
- [ ] Manual test successful locally
- [ ] Railway deployment successful
- [ ] Health check returns 200
- [ ] WhatsApp webhook test successful

## Rollback Plan

If something goes wrong:

1. **Immediate**: Disable webhook in Whapi/Meta
2. **Revert code**: Roll back to previous commit
3. **Fix issue locally**: Reproduce and fix
4. **Test thoroughly**: Before redeploying
5. **Redeploy**: With fixes

## Summary

### Success Criteria

✅ Phase 5 complete when:
- All quality checks pass
- Tests pass or run successfully
- Deployment to Railway successful
- Webhook receives messages
- Bot responds to WhatsApp messages
- Logs show no critical errors
- Health endpoint returns 200

### Production Monitoring

After deployment:
1. Monitor logs daily
2. Track API usage in Anthropic dashboard
3. Check WhatsApp delivery rates
4. Monitor response times
5. Update as needed

### Next Steps

After deployment:
1. **Monitor**: Check logs regularly
2. **Iterate**: Add new agents/features
3. **Scale**: Add database/caching as needed
4. **Maintain**: Keep dependencies updated

Your whatsapp-agentkit is now live! 🚀
