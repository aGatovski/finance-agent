/** Who sent a message in the chat. */
export type Role = 'user' | 'assistant'

/** A single chat message rendered in the conversation. */
export interface ChatMessage {
  id: string
  role: Role
  content: string
}
