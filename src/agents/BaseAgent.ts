import Anthropic from '@anthropic-ai/sdk';

export interface AgentConfig {
  name: string;
  description: string;
  systemPrompt: string;
  tools?: Anthropic.Tool[];
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export abstract class BaseAgent {
  protected name: string;
  protected description: string;
  protected systemPrompt: string;
  protected tools: Anthropic.Tool[];
  protected conversationHistory: Message[] = [];
  protected client: Anthropic;
  protected maxTokens = 1024;

  constructor(config: AgentConfig) {
    this.name = config.name;
    this.description = config.description;
    this.systemPrompt = config.systemPrompt;
    this.tools = config.tools || [];
    this.client = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY,
    });
  }

  /**
   * Process incoming message and return response
   */
  async handle(userMessage: string): Promise<string> {
    try {
      // Add user message to history
      this.conversationHistory.push({
        role: 'user',
        content: userMessage,
      });

      // Call Claude API
      const response = await this.client.messages.create({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: this.maxTokens,
        system: this.systemPrompt,
        messages: this.conversationHistory,
        tools: this.tools.length > 0 ? this.tools : undefined,
      });

      // Extract text response
      let assistantMessage = '';

      for (const block of response.content) {
        if (block.type === 'text') {
          assistantMessage += block.text;
        } else if (block.type === 'tool_use') {
          // Handle tool use if implemented in subclass
          const toolResult = await this.handleToolUse(block);
          assistantMessage += toolResult;
        }
      }

      // Add assistant response to history
      if (assistantMessage) {
        this.conversationHistory.push({
          role: 'assistant',
          content: assistantMessage,
        });
      }

      return assistantMessage;
    } catch (error) {
      console.error(`Agent ${this.name} error:`, error);
      return 'I encountered an error processing your message. Please try again.';
    }
  }

  /**
   * Handle tool use (override in subclass if needed)
   */
  protected async handleToolUse(
    toolUse: Anthropic.ToolUseBlock
  ): Promise<string> {
    console.log(`Tool call: ${toolUse.name}`, toolUse.input);
    return 'Tool execution not implemented';
  }

  /**
   * Reset conversation history
   */
  resetConversation(): void {
    this.conversationHistory = [];
  }

  /**
   * Get agent metadata
   */
  getMetadata() {
    return {
      name: this.name,
      description: this.description,
      tools: this.tools.map((t) => t.name),
    };
  }

  /**
   * Get conversation history
   */
  getHistory(): Message[] {
    return this.conversationHistory;
  }

  /**
   * Set max tokens for responses
   */
  setMaxTokens(tokens: number): void {
    this.maxTokens = Math.min(tokens, 4096);
  }
}

export default BaseAgent;
