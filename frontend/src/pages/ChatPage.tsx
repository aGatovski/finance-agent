import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { ChatMessage } from '../types/chat'
import { sendMessage } from '../api/chat'

const THREAD_KEY = 'finance-thread-id'

/** Read the current conversation id from localStorage, creating one if needed. */
function loadThreadId(): string {
  let id = localStorage.getItem(THREAD_KEY)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(THREAD_KEY, id)
  }
  return id
}

const SUGGESTIONS = [
  'How much did I spend last month?',
  'What are my top spending categories?',
  'Where can I cut back?',
]

/** Chat surface for the agent: send messages, see replies, reset the thread. */
export default function ChatPage() {
  const [threadId, setThreadId] = useState(loadThreadId)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  // Keep the latest message in view as the conversation grows.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function send(text: string) {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmed,
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const reply = await sendMessage(trimmed, threadId)
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: 'assistant', content: reply },
      ])
    } catch (err) {
      const detail = err instanceof Error ? err.message : 'Something went wrong'
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `⚠️ Could not reach the agent: ${detail}`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    void send(input)
  }

  /** Start a brand-new conversation (fresh thread id, cleared transcript). */
  function resetConversation() {
    const id = crypto.randomUUID()
    localStorage.setItem(THREAD_KEY, id)
    setThreadId(id)
    setMessages([])
  }

  return (
    <div className="chat">
      <header className="chat-header">
        <h2>Finance Assistant</h2>
        <button type="button" className="text-btn" onClick={resetConversation}>
          New chat
        </button>
      </header>

      <div className="messages">
        {messages.length === 0 && !loading ? (
          <div className="empty">
            <p>Ask me anything about your finances.</p>
            <div className="suggestions">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  className="chip"
                  onClick={() => void send(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => (
            <div key={m.id} className={`msg ${m.role}`}>
              {m.content}
            </div>
          ))
        )}

        {loading && (
          <div className="msg assistant typing">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}

        <div ref={endRef} />
      </div>

      <form className="composer" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Type a message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <button
          type="submit"
          className="send-btn"
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </form>
    </div>
  )
}
