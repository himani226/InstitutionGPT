// Strip filename extension for cleaner source labels
const cleanSource = (s) => s.replace(/\.(txt|pdf|csv|md)$/i, '').replace(/_/g, ' ')

function TypingIndicator() {
  return (
    <div className="msg-row assistant">
      <div className="typing-wrap" aria-label="Assistant is typing">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </div>
  )
}

function UserBubble({ content }) {
  return (
    <div className="msg-row user">
      <div className="bubble-user">{content}</div>
    </div>
  )
}

function AssistantBubble({ content, agent, sources = [], isStreaming }) {
  // Show typing dots until first tokens arrive
  if (isStreaming && !content) return <TypingIndicator />

  return (
    <div className="msg-row assistant">
      <div className="bubble-assistant">
        {/* Agent label */}
        {agent && (
          <div className="agent-tag">
            <span className="agent-dot" aria-hidden="true" />
            {agent}
          </div>
        )}

        {/* Message text + streaming cursor */}
        <p className="bubble-text">
          {content}
          {isStreaming && <span className="cursor" aria-hidden="true" />}
        </p>

        {/* Source badges — only show when done streaming */}
        {!isStreaming && sources.length > 0 && (
          <div className="sources" aria-label="Sources">
            {sources.map(src => (
              <span key={src} className="source-chip">
                {cleanSource(src)}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function MessageBubble({ message }) {
  if (message.type === 'user') {
    return <UserBubble content={message.content} />
  }
  return (
    <AssistantBubble
      content={message.content}
      agent={message.agent}
      sources={message.sources}
      isStreaming={message.isStreaming}
    />
  )
}