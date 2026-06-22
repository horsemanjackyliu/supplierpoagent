'use client'

import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { Send, RefreshCw, Sparkles } from 'lucide-react'
import clsx from 'clsx'
import MessageBubble from './MessageBubble'
import SuggestedQuestions from './SuggestedQuestions'

export interface Message {
  id: string
  role: 'user' | 'agent'
  text: string
  timestamp: Date
}

const SUGGESTED = [
  'Show me all my open purchase orders',
  'What is the delivery status for PO 4500001234?',
  'List POs with delivery date this week',
  'Show line items for my latest purchase order',
  'Which POs are overdue for goods receipt?',
]

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`
    }
  }, [input])

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return
    setError(null)

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      text: text.trim(),
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text.trim(), sessionId }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.error || `HTTP ${res.status}`)
      }

      if (data.sessionId) setSessionId(data.sessionId)

      const agentMsg: Message = {
        id: `a-${Date.now()}`,
        role: 'agent',
        text: data.reply,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, agentMsg])
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Something went wrong'
      setError(msg)
      setMessages((prev) => [
        ...prev,
        {
          id: `e-${Date.now()}`,
          role: 'agent',
          text: `⚠️ ${msg}`,
          timestamp: new Date(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const handleReset = () => {
    setMessages([])
    setSessionId(null)
    setError(null)
    setInput('')
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto w-full px-4 pb-4">
      {/* Conversation area */}
      <div className="flex-1 overflow-y-auto chat-scroll pt-6 pb-2 space-y-4">
        {isEmpty ? (
          <WelcomeScreen onSelect={sendMessage} suggestions={SUGGESTED} />
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {loading && <TypingIndicator />}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* Input bar */}
      <div className="sap-card mt-3 p-2 flex items-end gap-2">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your purchase orders…"
          rows={1}
          className="flex-1 resize-none sap-input border-0 focus:ring-0 focus:border-0 py-1.5 px-2 text-sm leading-snug"
          disabled={loading}
        />
        <div className="flex items-center gap-1 pb-0.5">
          {!isEmpty && (
            <button
              onClick={handleReset}
              title="New conversation"
              className="sap-btn-ghost p-1.5 rounded"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            className="sap-btn-primary py-1.5 px-3 flex items-center gap-1"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </div>

      <p className="text-center text-xs text-sap-gray-400 mt-1.5">
        Queries run against live SAP S/4HANA data &mdash; results are real-time.
      </p>
    </div>
  )
}

function WelcomeScreen({
  onSelect,
  suggestions,
}: {
  onSelect: (q: string) => void
  suggestions: string[]
}) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-8 py-12">
      <div className="flex flex-col items-center gap-3 text-center">
        <div className="w-14 h-14 rounded-full bg-sap-blue-light flex items-center justify-center border border-sap-blue/20">
          <Sparkles className="w-7 h-7 text-sap-blue" />
        </div>
        <h1 className="text-xl font-semibold text-sap-gray-800">
          Supplier PO Assistant
        </h1>
        <p className="text-sap-gray-600 text-sm max-w-sm">
          Ask me about your open purchase orders, delivery status, line items,
          or any PO details from SAP S/4HANA.
        </p>
      </div>

      <SuggestedQuestions questions={suggestions} onSelect={onSelect} />
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex gap-3 items-end">
      <div className="w-7 h-7 rounded-full bg-sap-blue-light border border-sap-blue/20 flex items-center justify-center flex-shrink-0">
        <Sparkles className="w-3.5 h-3.5 text-sap-blue" />
      </div>
      <div className="message-agent flex items-center gap-1.5 py-3 px-4">
        <span className="typing-dot" style={{ animationDelay: '0ms' }} />
        <span className="typing-dot" style={{ animationDelay: '150ms' }} />
        <span className="typing-dot" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  )
}
