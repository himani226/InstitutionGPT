import { useRef, useState } from 'react'

const ROLE_HINTS = {
  student: 'Ask about fees, courses, exams, hostel…',
  faculty: 'Ask about research, leave, pay scales…',
  admin:   'Ask about certificates, IT, transport…',
}

export default function InputBar({ onSend, isLoading, role }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  const handleInput = (e) => {
    setValue(e.target.value)
    // Auto-resize textarea
    const ta = textareaRef.current
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 120) + 'px'
  }

  const handleSend = () => {
    const query = value.trim()
    if (!query || isLoading) return
    setValue('')
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    onSend(query)
  }

  const handleKeyDown = (e) => {
    // Enter sends; Shift+Enter inserts newline
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <footer className="input-bar">
      <div className="input-wrap">
        <textarea
          ref={textareaRef}
          className="chat-input"
          rows={1}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={ROLE_HINTS[role] ?? 'Ask anything…'}
          disabled={isLoading}
          aria-label="Type your message"
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={isLoading || !value.trim()}
          aria-label="Send message"
        >
          {isLoading ? '⏳' : '↑'}
        </button>
      </div>
      <p className="input-hint">
        Enter to send · Shift+Enter for newline · Powered by Groq Llama&nbsp;3
      </p>
    </footer>
  )
}