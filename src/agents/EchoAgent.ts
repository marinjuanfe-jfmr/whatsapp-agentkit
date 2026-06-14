import BaseAgent, { AgentConfig } from './BaseAgent';

/**
 * Simple Echo Agent for testing
 * Repeats messages back to verify communication
 */
export class EchoAgent extends BaseAgent {
  constructor() {
    const config: AgentConfig = {
      name: 'echo-agent',
      description: 'Echo agent for testing message flow',
      systemPrompt: `You are an echo agent. Your job is to confirm that you received the user's message by repeating it back in a friendly way.

Keep responses short and simple. If the user asks a question, simply confirm you received it.`,
    };

    super(config);
  }
}

export default EchoAgent;
