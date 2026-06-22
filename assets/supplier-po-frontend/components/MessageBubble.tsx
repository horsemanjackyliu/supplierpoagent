'use client'

import { Sparkles } from 'lucide-react'
import type { Message } from './Chat'

interface Props {
  message: Message
}

/**
 * Renders markdown-light text:
 *  - **bold**
 *  - `code`
 *  - lines starting with - or * as list items
 *  - blank lines as paragraph breaks
 */
function formatText(text: string): React.ReactNode[] {
  const lines = text.split('\n')
  const nodes: React.ReactNode[] = []
  let key = 0

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    if (line.trim() === '') {
      nodes.push(<br key={key++} />)
      continue
    }

    // List item
    const isList = /^(\s*[-*•])\s+/.test(line)
    const content = isList ? line.replace(/^\s*[-*•]\s+/, '') : line

    const rendered = renderInline(content, key)
    key += 100

    if (isList) {
      nodes.push(
        <div key={key++} className="flex gap-1.5 my-0.5">
          <span className="text-sap-blue mt-0.5">•</span>
          <span>{rendered}</span>
        </div>
      )
    } else {
      nodes.push(<span key={key++}>{rendered}{' '}</span>)
    }
  }
  return nodes
}

function renderInline(text: string, baseKey: number): React.ReactNode[] {
  // Split on **bold** and `code`
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={baseKey + i}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code
          key={baseKey + i}
          className="bg-sap-gray-200 text-sap-gray-800 px-1 rounded text-xs font-mono"
        >
          {part.slice(1, -1)}
        </code>
      )
    }
    return <span key={baseKey + i}>{part}</span>
  })
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  const time = message.timestamp.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div className={`flex gap-3 items-end ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-sap-blue-light border border-sap-blue/20 flex items-center justify-center flex-shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-sap-blue" />
        </div>
      )}

      <div className={`flex flex-col gap-0.5 ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={isUser ? 'message-user' : 'message-agent'}>
          {isUser ? (
            <span>{message.text}</span>
          ) : (
            <span className="whitespace-pre-wrap">{formatText(message.text)}</span>
          )}
        </div>
        <span className="text-sap-gray-400 text-[10px] px-1">{time}</span>
      </div>
    </div>
  )
}
