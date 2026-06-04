import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'

const SUGGESTIONS = [
  'Last date to apply for B.Tech admissions?',
  'What is the fee for B.Tech CSE per semester?',
  'What subjects are in Semester 5 of B.Tech CSE?',
  'What is the hostel curfew time on weekdays?',
  'What is the SCI journal publication incentive for faculty?',
]

function EmptyState({ onSuggestion, role }) {
  const greeting = {
    student: 'Ask me about fees, courses, timetables, or admissions.',
    faculty: 'Ask me about pay scales, research incentives, or leave policies.',
    admin:   'Ask me about certificates, portals, transport, or procurement.',
  }[role] ?? 'Ask me anything about Northfield University.'

  return (
    <div className="empty-state">
      <div className="empty-glyph" aria-hidden="true">🎓</div>
      <div>
        <p className="empty-title">How can I help you?</p>
        <p className="empty-body">{greeting}</p>
      </div>

      <p className="suggestions-label">Try asking</p>
      <div className="suggestions">
        {SUGGESTIONS.map(q => (
          <button
            key={q}
            className="suggestion-btn"
            onClick={() => onSuggestion(q)}
          >
            <span className="suggestion-arrow">↗</span>
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}

export default function ChatWindow({ messages, onSuggestion, role }) {
  const bottomRef = useRef(null)

  // Auto-scroll to bottom on every new message or token
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const isWelcomeOnly =
    messages.length === 1 && messages[0].id === 'welcome'

  return (
    <main className="chat-window" aria-label="Chat messages">
      {isWelcomeOnly ? (
        <EmptyState onSuggestion={onSuggestion} role={role} />
      ) : (
        <>
          {messages
            .filter(m => m.id !== 'welcome')
            .map(m => (
              <MessageBubble key={m.id} message={m} />
            ))}
        </>
      )}
      <div ref={bottomRef} />
    </main>
  )
}