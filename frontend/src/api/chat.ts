/**
 * Chat API client.
 *
 * The agent owns conversation history via its checkpointer, so we only send the
 * latest message plus a `thread_id` identifying the conversation.
 */

import { request } from './client'

interface ChatResponse {
  reply: string
}

/** Send one message to the agent and return its reply. */
export async function sendMessage(message: string, threadId: string): Promise<string> {
  const data = await request<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify({ message, thread_id: threadId }),
  })
  return data.reply
}
