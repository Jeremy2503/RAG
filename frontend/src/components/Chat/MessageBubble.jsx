import { User, Sparkles, Briefcase, Users, Search, Copy, ThumbsUp, ThumbsDown } from 'lucide-react'
import { useState } from 'react'

const MessageBubble = ({ message }) => {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'
  
  const getAgentIcon = () => {
    if (isUser) return <User size={20} />
    
    const agentType = message.agent_type
    
    switch (agentType) {
      case 'it_policy':
        return <Briefcase size={20} />
      case 'hr_policy':
        return <Users size={20} />
      case 'research':
        return <Search size={20} />
      default:
        return <Sparkles size={20} />
    }
  }

  const getAgentLabel = () => {
    if (isUser) return 'You'
    
    const agentType = message.agent_type
    
    switch (agentType) {
      case 'it_policy':
        return 'IT Policy Agent'
      case 'hr_policy':
        return 'HR Policy Agent'
      case 'research':
        return 'Research Agent'
      case 'coordinator':
        return 'Coordinator'
      default:
        return 'AI Assistant'
    }
  }

  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return ''
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={`modern-message-bubble ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-avatar">
        {getAgentIcon()}
      </div>
      
      <div className="message-body">
        <div className="message-header-modern">
          <span className="message-sender-modern">{getAgentLabel()}</span>
          {message.timestamp && (
            <span className="message-time-modern">{formatTimestamp(message.timestamp)}</span>
          )}
        </div>
        
        <div className="message-content-modern">
          {message.content}
        </div>

        {message.metadata?.sources_count > 0 && (
          <div className="message-sources-modern">
            <span className="sources-icon">📚</span>
            <span>{message.metadata.sources_count} source{message.metadata.sources_count > 1 ? 's' : ''} referenced</span>
          </div>
        )}

        {!isUser && (
          <div className="message-actions">
            <button 
              className={`action-btn ${copied ? 'copied' : ''}`}
              onClick={handleCopy}
              title={copied ? 'Copied!' : 'Copy message'}
            >
              <Copy size={16} />
            </button>
            <button className="action-btn" title="Good response">
              <ThumbsUp size={16} />
            </button>
            <button className="action-btn" title="Bad response">
              <ThumbsDown size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default MessageBubble
