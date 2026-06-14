# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**whatsapp-agentkit** is a framework for building autonomous agents that interact through WhatsApp. It provides infrastructure for creating multi-agent systems that can communicate, coordinate, and execute tasks via WhatsApp messaging.

## Quick Start

### Setup
```bash
npm install          # Install dependencies
npm run setup        # Initialize environment and configuration
```

### Development
```bash
npm run dev          # Start development server with auto-reload
npm run build        # Build production bundle
npm start            # Run production build
```

### Quality & Testing
```bash
npm test             # Run full test suite
npm run test:watch   # Run tests in watch mode
npm run test:coverage # Generate coverage report
npm run lint         # Run linter (ESLint)
npm run lint:fix     # Auto-fix linting issues
npm run type-check   # Run TypeScript type checking
```

### Deployment
```bash
npm run deploy       # Deploy to production (Railway/configured platform)
```

## Architecture Overview

### Core Components

1. **Agent System** (`src/agents/`)
   - Base Agent class with lifecycle management
   - Agent registry for discovery and instantiation
   - Message routing and handler system
   - State management per agent instance

2. **Transport Layer** (`src/transports/`)
   - WhatsApp transport adapter (integrates with WhatsApp/Whapi provider)
   - Message encoding/decoding
   - Connection lifecycle management
   - Error handling and reconnection logic

3. **Message Processing** (`src/messaging/`)
   - Message parser for incoming WhatsApp messages
   - Response formatter for WhatsApp constraints
   - Command dispatcher
   - Intent recognition

4. **Tools & Integrations** (`src/tools/`)
   - Reusable tool definitions (web search, API calls, file operations)
   - Tool execution sandbox
   - Error handling for tool failures

5. **Claude Integration** (`src/claude/`)
   - Anthropic SDK wrapper
   - Prompt management and templating
   - Token counting and optimization
   - Conversation history management

### Data Flow

```
WhatsApp Message
    ↓
Transport Layer (receive)
    ↓
Message Parser
    ↓
Agent Router (determines target agent)
    ↓
Agent Handler (processes with Claude)
    ↓
Tool Execution (if needed)
    ↓
Response Formatter
    ↓
Transport Layer (send)
    ↓
WhatsApp User
```

## Onboarding: 5-Phase Setup Flow

### Phase 1: Environment Configuration
- **Goal**: Set up credentials and basic configuration
- **Tasks**:
  - Create `.env` file with:
    - `ANTHROPIC_API_KEY`: Claude API key
    - `WHATSAPP_PHONE_NUMBER`: Bot's WhatsApp number
    - `WHATSAPP_AUTH_TOKEN`: Authentication token (if applicable)
    - `PORT`: Server port (default: 3000)
  - Verify `.env.example` exists as reference
  - Validate all required keys are set

### Phase 2: Project Structure Setup
- **Goal**: Initialize project directories and core files
- **Tasks**:
  - Create directory structure:
    - `src/agents/` - Agent implementations
    - `src/transports/` - WhatsApp transport
    - `src/messaging/` - Message handling
    - `src/tools/` - Available tools for agents
    - `src/claude/` - Claude integration
    - `tests/` - Test files
    - `config/` - Configuration files
  - Create base agent class template
  - Create transport adapter template
  - Generate TypeScript configuration

### Phase 3: WhatsApp Integration
- **Goal**: Establish WhatsApp connection and message flow
- **Tasks**:
  - Configure WhatsApp transport with Whapi provider credentials
  - Implement message receive webhook (`POST /webhook`)
  - Implement message send mechanism
  - Test connection with echo agent
  - Verify message delivery and receipt
  - Set up webhook signature validation

### Phase 4: Agent Development
- **Goal**: Create and configure your first agent
- **Tasks**:
  - Create agent directory: `src/agents/example-agent/`
  - Implement agent class extending BaseAgent
  - Define agent capabilities and system prompt
  - Register agent in agent registry
  - Create test cases for agent behavior
  - Validate agent responds to messages

### Phase 5: Testing & Deployment
- **Goal**: Prepare for production
- **Tasks**:
  - Run full test suite (`npm test`)
  - Verify type safety (`npm run type-check`)
  - Check linting (`npm run lint`)
  - Test multi-agent coordination (if multiple agents)
  - Review environment configuration for production
  - Deploy to production (`npm run deploy`)
  - Monitor logs and error tracking
  - Set up alerting for agent failures

## Key Files & Directories

- `src/` - Source code
  - `agents/` - Agent implementations
  - `transports/` - Transport adapters
  - `messaging/` - Message handling
  - `tools/` - Tool definitions
  - `claude/` - Claude API integration
  - `index.ts` - Main entry point
- `tests/` - Test files (Jest)
- `config/` - Configuration defaults
- `.env.example` - Environment variable template
- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration

## Important Constraints & Patterns

### Message Handling
- WhatsApp has a 4096 character message limit; responses longer than this must be split
- Media messages (images, documents) require special handling with WhatsApp media URLs
- Message timestamps are critical for conversation context—always preserve them

### Agent Lifecycle
- Agents are instantiated per conversation thread (by phone number)
- Agent state persists in-memory; implement persistence for production use
- Agent initialization should be fast to avoid WhatsApp timeout (default ~30s per request)

### Claude Integration
- Always include system prompt for consistent agent behavior
- Use tool_choice="auto" for agents that need tool access
- Implement token counting to stay within model limits
- Messages over ~50 KB should use file uploads instead of direct text

### Error Handling
- Network errors (WhatsApp connectivity) should implement exponential backoff
- Claude API errors should not crash the agent—return a friendly error message
- Tool execution failures should be caught and passed back to Claude for retry logic

## Dependencies

- **Core**: express, axios, dotenv
- **AI**: @anthropic-ai/sdk
- **Transport**: WhatsApp API client (Whapi SDK or similar)
- **Development**: TypeScript, Jest, ESLint, Prettier
- **Deployment**: Node.js 18+, Railway (or configured platform)

## Common Development Tasks

### Adding a New Agent
1. Create directory: `src/agents/my-agent/`
2. Create `MyAgent.ts` extending `BaseAgent`
3. Define system prompt and capabilities
4. Register in `src/agents/index.ts`
5. Add tests in `tests/agents/MyAgent.test.ts`
6. Test locally with `npm run dev`

### Adding a New Tool
1. Create file: `src/tools/my-tool.ts`
2. Export tool definition matching Anthropic SDK format
3. Implement tool handler with error handling
4. Register in agent's tool list
5. Add tests for tool behavior

### Debugging Agent Behavior
- Set `DEBUG=agentkit:*` environment variable for detailed logs
- Check agent state with `/debug <agent-name>` command
- Review Claude API request/response in logs
- Test with simple message first to isolate issues

## Environment Variables

Required:
- `ANTHROPIC_API_KEY` - Claude API key from console.anthropic.com
- `WHATSAPP_PHONE_NUMBER` - Bot's WhatsApp number
- `PORT` - Server port (default 3000)

Optional:
- `DEBUG` - Debug logging pattern (e.g., `agentkit:*`)
- `NODE_ENV` - Environment (development/production)
- `LOG_LEVEL` - Logging level (debug/info/warn/error)
- `WHATSAPP_AUTH_TOKEN` - For secured transport (if needed)

## Deployment Notes

- Deploy to Railway: `railway up` (requires Railway CLI)
- Set production environment variables in Railway dashboard
- Ensure webhook URL is publicly accessible
- Monitor CloudWatch or Railway logs for errors
- Keep `NODE_ENV=production` for optimized builds

## References

- [Anthropic Claude API](https://docs.anthropic.com/)
- [WhatsApp Business Platform](https://developers.facebook.com/docs/whatsapp)
- [Railway Deployment](https://railway.app/docs)
