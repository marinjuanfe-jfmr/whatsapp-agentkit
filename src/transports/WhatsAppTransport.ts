import axios, { AxiosInstance } from 'axios';

export interface WhatsAppMessage {
  from: string;
  to: string;
  text: string;
  timestamp: number;
  messageId: string;
}

export interface WhatsAppResponse {
  success: boolean;
  messageId?: string;
  error?: string;
}

export class WhatsAppTransport {
  private client: AxiosInstance;
  private apiToken: string;
  private phoneNumber: string;
  private baseUrl = 'https://api.whapi.io';

  constructor(apiToken: string, phoneNumber: string) {
    this.apiToken = apiToken;
    this.phoneNumber = phoneNumber;

    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        Authorization: `Bearer ${apiToken}`,
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Send text message via WhatsApp
   */
  async sendMessage(to: string, text: string): Promise<WhatsAppResponse> {
    try {
      // Split message if it exceeds WhatsApp limit (4096 chars)
      const messages = this.splitMessage(text);

      const responses: WhatsAppResponse[] = [];

      for (const message of messages) {
        const response = await this.client.post('/messages/text', {
          to,
          body: message,
        });

        responses.push({
          success: true,
          messageId: response.data?.message?.id,
        });
      }

      return responses[0]; // Return first response
    } catch (error) {
      console.error('WhatsApp send error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Send media message via WhatsApp
   */
  async sendMedia(
    to: string,
    mediaUrl: string,
    mediaType: 'image' | 'document' | 'audio' | 'video',
    caption?: string
  ): Promise<WhatsAppResponse> {
    try {
      const payload: Record<string, unknown> = {
        to,
        [mediaType]: {
          link: mediaUrl,
        },
      };

      if (caption && ['image', 'document', 'video'].includes(mediaType)) {
        payload.caption = caption;
      }

      const response = await this.client.post(`/messages/${mediaType}`, payload);

      return {
        success: true,
        messageId: response.data?.message?.id,
      };
    } catch (error) {
      console.error('WhatsApp media send error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Parse incoming webhook message
   */
  parseWebhookMessage(data: unknown): WhatsAppMessage | null {
    try {
      const webhook = data as Record<string, unknown>;

      // Handle Whapi format
      if (webhook.messages?.length > 0) {
        const message = webhook.messages[0] as Record<string, unknown>;
        return {
          from: message.from as string,
          to: message.to as string,
          text: message.text?.body as string,
          timestamp: message.timestamp as number,
          messageId: message.id as string,
        };
      }

      return null;
    } catch (error) {
      console.error('Failed to parse webhook message:', error);
      return null;
    }
  }

  /**
   * Verify webhook signature (implement based on provider)
   */
  verifyWebhookSignature(
    payload: string,
    signature: string
  ): boolean {
    // Whapi uses token-based verification
    // For production, implement proper HMAC verification
    return true; // Simplified for now
  }

  /**
   * Check connection status
   */
  async checkConnection(): Promise<boolean> {
    try {
      const response = await this.client.get('/contacts/list');
      return response.status === 200;
    } catch (error) {
      console.error('Connection check failed:', error);
      return false;
    }
  }

  /**
   * Get bot info
   */
  async getBotInfo(): Promise<Record<string, unknown>> {
    try {
      const response = await this.client.get('/me');
      return response.data;
    } catch (error) {
      console.error('Failed to get bot info:', error);
      return {};
    }
  }

  /**
   * Split long messages to respect WhatsApp limits
   */
  private splitMessage(text: string, limit = 4096): string[] {
    if (text.length <= limit) {
      return [text];
    }

    const messages: string[] = [];
    let currentMessage = '';

    const words = text.split(' ');

    for (const word of words) {
      if ((currentMessage + word).length > limit) {
        if (currentMessage) {
          messages.push(currentMessage.trim());
          currentMessage = '';
        }
        if (word.length > limit) {
          // Split very long words
          for (let i = 0; i < word.length; i += limit) {
            messages.push(word.substring(i, i + limit));
          }
        } else {
          currentMessage = word + ' ';
        }
      } else {
        currentMessage += word + ' ';
      }
    }

    if (currentMessage.trim()) {
      messages.push(currentMessage.trim());
    }

    return messages;
  }
}

export default WhatsAppTransport;
