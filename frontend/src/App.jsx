import { useState, useCallback, useRef } from 'react'
import Header      from './components/Header'
import ChatWindow  from './components/ChatWindow'
import InputBar    from './components/InputBar'
import { streamMessage } from './api/client'

// Stable ID for the welcome placeholder (never shown as a bubble)
const WELCOME_ID = 'welcome'

const mkId = () => `${Date.now()}-${Math.random().toString(36).slice(2)}`

export default function App() {
  const [messages,   setMessages]   = useState([{ id: WELCOME_ID }])
  const [role,       setRole]       = useState('student')
  const [isLoading,  setIsLoading]  = useState(false)
  const [sessionId,  setSessionId]  = useState(
    () => localStorage.getItem('igpt_session') ?? null
  )

  // Abort controller ref — cancels the in-flight stream when role changes
  const abortRef = useRef(null)

  // When the user switches role, cancel any active stream
  const handleRoleChange = (newRole) => {
    abortRef.current?.abort()
    setRole(newRole)
  }

  const handleClear = () => {
    abortRef.current?.abort()
    setMessages([{ id: WELCOME_ID }])
    setSessionId(null)
    localStorage.removeItem('igpt_session')
    setIsLoading(false)
  }

  const sendMessage = useCallback(async (query) => {
    if (!query.trim() || isLoading) return

    // Cancel any existing stream
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    const userId      = mkId()
    const assistantId = mkId()

    // Immediately add user bubble + empty assistant placeholder
    setMessages(prev => [
      ...prev.filter(m => m.id !== WELCOME_ID),
      { id: userId,      type: 'user',      content: query,     timestamp: new Date() },
      { id: assistantId, type: 'assistant', content: '',        agent: '', sources: [], isStreaming: true, timestamp: new Date() },
    ])
    setIsLoading(true)

    try {
      let sid = sessionId

      for await (const event of streamMessage(query, role, sid, ctrl.signal)) {

        if (event.type === 'meta') {
          // Persist session ID and update agent/sources on the placeholder
          sid = event.session_id
          setSessionId(sid)
          localStorage.setItem('igpt_session', sid)
          setMessages(prev => prev.map(m =>
            m.id === assistantId
              ? { ...m, agent: event.agent, sources: event.sources }
              : m
          ))

        } else if (event.type === 'token') {
          // Append streamed token
          setMessages(prev => prev.map(m =>
            m.id === assistantId
              ? { ...m, content: m.content + event.content }
              : m
          ))

        } else if (event.type === 'done') {
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? { ...m, isStreaming: false } : m
          ))

        } else if (event.type === 'error') {
          setMessages(prev => prev.map(m =>
            m.id === assistantId
              ? { ...m, content: `⚠ ${event.message}`, isStreaming: false }
              : m
          ))
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') return  // user cancelled — silent

      setMessages(prev => prev.map(m =>
        m.id === assistantId
          ? {
              ...m,
              content:     'Could not reach the API server. Make sure it\'s running on port 8000.',
              isStreaming: false,
            }
          : m
      ))
    } finally {
      setIsLoading(false)
    }
  }, [role, sessionId, isLoading])

  return (
    <div className="app">
      <Header
        role={role}
        onRoleChange={handleRoleChange}
        onClear={handleClear}
      />
      <ChatWindow
        messages={messages}
        onSuggestion={sendMessage}
        role={role}
      />
      <InputBar
        onSend={sendMessage}
        isLoading={isLoading}
        role={role}
      />
    </div>
  )
}