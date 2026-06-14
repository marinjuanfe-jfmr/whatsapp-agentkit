# Phase 4: Agent Development

## Overview
Create and configure your first custom agent. Build agents specific to your use case.

## Prerequisites
- Phase 1-3 completed
- Server can run with `npm run dev`
- EchoAgent working for basic message flow

## Understanding Agents

### Agent Architecture

An agent is a class that extends `BaseAgent` and implements Claude-powered message handling:

```
User Message (WhatsApp)
    ↓
Agent.handle(message)
    ↓
Claude API call
    ↓
Response formatted
    ↓
Agent.handle() returns string
    ↓
Response sent to WhatsApp
```

### Key Properties

- **name**: Unique identifier (e.g., "real-estate-agent")
- **description**: Human-readable description
- **systemPrompt**: Instructions for Claude on how to behave
- **tools**: Optional Claude tools the agent can use
- **conversationHistory**: Maintains context across messages

## Example 1: Creating a Real Estate Agent

For your "Los Robles 2026" property business:

### Step 1: Create Agent File

Create `src/agents/RealEstateAgent.ts`:

```typescript
import BaseAgent, { AgentConfig } from './BaseAgent';

export class RealEstateAgent extends BaseAgent {
  constructor() {
    const config: AgentConfig = {
      name: 'real-estate-agent',
      description: 'Real estate agent for Los Robles properties',
      systemPrompt: `You are a professional real estate agent for Los Robles properties.

Your responsibilities:
- Answer questions about available properties
- Provide property details (location, price, amenities)
- Schedule viewings
- Provide market information
- Be friendly and professional

Available Properties:
- Los Robles Estate: 5BR/3BA, $450K
- Sunset Heights: 3BR/2BA, $280K
- Ocean View Villa: 4BR/3BA, $620K

Always ask follow-up questions to understand customer needs.
Be ready to schedule a viewing or connect with a sales agent.`,
    };

    super(config);
    this.setMaxTokens(1024);
  }
}

export default RealEstateAgent;
```

### Step 2: Register Agent

Update `src/index.ts` to use your agent:

```typescript
import RealEstateAgent from './agents/RealEstateAgent';

// Initialize agents
const realEstateAgent = new RealEstateAgent();

// In webhook handler, replace:
// const response = await echoAgent.handle(message.text);
// With:
const response = await realEstateAgent.handle(message.text);
```

### Step 3: Test Agent

```bash
# Start server
npm run dev

# Test in another terminal
curl -X POST http://localhost:3000/test \
  -H "Content-Type: application/json" \
  -d '{"message": "What properties do you have available?"}'
```

Expected: Agent describes Los Robles properties.

## Example 2: Agent with Tools

Create `src/agents/SearchAgent.ts` with web search capability:

```typescript
import BaseAgent, { AgentConfig } from './BaseAgent';
import Anthropic from '@anthropic-ai/sdk';

export class SearchAgent extends BaseAgent {
  constructor() {
    // Define tools
    const tools: Anthropic.Tool[] = [
      {
        name: 'search_web',
        description: 'Search the web for information',
        input_schema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Search query',
            },
          },
          required: ['query'],
        },
      },
    ];

    const config: AgentConfig = {
      name: 'search-agent',
      description: 'Agent with web search capability',
      systemPrompt: `You are a helpful assistant with access to web search.
Use the search_web tool to find current information when needed.`,
      tools,
    };

    super(config);
  }

  protected async handleToolUse(
    toolUse: Anthropic.ToolUseBlock
  ): Promise<string> {
    if (toolUse.name === 'search_web') {
      const input = toolUse.input as { query: string };
      console.log(`Searching for: ${input.query}`);
      // Implement actual web search here
      return `Search results for: ${input.query}`;
    }
    return 'Unknown tool';
  }
}

export default SearchAgent;
```

## Creating Custom System Prompts

### Best Practices

1. **Be specific** about the agent's role
2. **List available information** the agent can reference
3. **Define response format** (short/long, formal/casual)
4. **Set boundaries** on what the agent can do
5. **Include examples** of good responses

### Example System Prompt

```
You are a customer support agent for an e-commerce store.

Your responsibilities:
- Answer questions about products
- Help with order tracking
- Process returns and refunds
- Escalate complex issues to human support

Product Database:
[List your products here]

Response Guidelines:
- Keep responses under 4000 characters (WhatsApp limit)
- Be friendly and professional
- Always offer alternatives if you can't help
- Ask for order number when discussing orders

When to escalate to human:
- Complaints about damaged goods
- Custom requests not in policy
- Billing disputes
```

## Multi-Agent Setup

To use multiple agents based on user input:

```typescript
// In src/index.ts
import RealEstateAgent from './agents/RealEstateAgent';
import SupportAgent from './agents/SupportAgent';

const realEstateAgent = new RealEstateAgent();
const supportAgent = new SupportAgent();

// Route to appropriate agent
function selectAgent(message: string) {
  if (
    message.toLowerCase().includes('property') ||
    message.toLowerCase().includes('house')
  ) {
    return realEstateAgent;
  } else if (
    message.toLowerCase().includes('support') ||
    message.toLowerCase().includes('help')
  ) {
    return supportAgent;
  }
  return realEstateAgent; // Default
}

// In webhook handler
const selectedAgent = selectAgent(message.text);
const response = await selectedAgent.handle(message.text);
```

## Testing Agents

### Local Testing

```bash
# Test with curl
curl -X POST http://localhost:3000/test \
  -H "Content-Type: application/json" \
  -d '{"message": "Your message here"}'
```

### Check Agent Info

```bash
curl http://localhost:3000/agent
```

Response shows:
- Agent name and description
- Available tools
- Conversation history length

### Monitor Conversation History

```typescript
// Get conversation history
const history = agent.getHistory();
console.log(history);
// [{role: 'user', content: '...'}, {role: 'assistant', content: '...'}]
```

## Common Agent Patterns

### 1. FAQ Agent
```typescript
const systemPrompt = `You are a FAQ chatbot.
Frequently Asked Questions:
1. Q: How do I reset my password? A: Click 'Forgot Password' on login page
2. Q: What's your shipping policy? A: [your policy]
...`;
```

### 2. Sales Agent
```typescript
const systemPrompt = `You are a sales representative.
Your goal is to:
1. Understand customer needs
2. Recommend relevant products
3. Answer pricing questions
4. Schedule demos or meetings`;
```

### 3. Customer Support
```typescript
const systemPrompt = `You are a customer support specialist.
- Help resolve customer issues
- Provide technical support
- Process refunds within policy
- Escalate complex issues`;
```

### 4. Lead Qualification
```typescript
const systemPrompt = `You are a sales development rep.
Qualify leads by asking:
- Company size
- Budget
- Use case
- Timeline
Then pass qualified leads to sales team`;
```

## Best Practices

### 1. System Prompt Quality
- Clear, concise instructions
- Examples of good responses
- Defined boundaries
- Reference material when needed

### 2. Token Management
- Set appropriate `maxTokens`
- Monitor conversation history length
- Reset history for new customers

### 3. Error Handling
- Handle Claude API errors gracefully
- Provide fallback responses
- Log errors for debugging

### 4. Testing Before Production
```bash
# Test locally
npm run dev

# Test various inputs
curl -X POST http://localhost:3000/test \
  -d '{"message": "boundary case 1"}'

curl -X POST http://localhost:3000/test \
  -d '{"message": "boundary case 2"}'
```

## File Structure

After creating custom agents:

```
src/agents/
├── BaseAgent.ts
├── EchoAgent.ts
├── RealEstateAgent.ts        # Your custom agent
├── SupportAgent.ts           # Another agent
└── README.md
```

## Next Steps

1. Create your first custom agent
2. Test with `npm run dev` and `/test` endpoint
3. Update agent in `src/index.ts`
4. Test with various inputs
5. When satisfied, proceed to Phase 5

Remember: Start simple, iterate, and add complexity as needed!
