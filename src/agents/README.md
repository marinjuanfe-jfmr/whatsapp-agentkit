# Agents

Base agent implementations for whatsapp-agentkit.

## Structure

- `BaseAgent.ts` - Abstract base class for all agents
- `AgentRegistry.ts` - Registers and instantiates agents
- Each agent in its own directory

## Creating a New Agent

1. Create directory: `src/agents/my-agent/`
2. Create class extending `BaseAgent`
3. Register in `AgentRegistry`
4. Add tests in `tests/agents/`

## Example

```typescript
import BaseAgent from '../BaseAgent';

export default class MyAgent extends BaseAgent {
  constructor() {
    super('my-agent', 'My Agent Description');
  }

  async handle(message: string): Promise<string> {
    // Handle incoming message
    return 'Response';
  }
}
```
