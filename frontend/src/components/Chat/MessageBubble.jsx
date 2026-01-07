import { User, Sparkles, Briefcase, Users, Search, Copy, ThumbsUp, ThumbsDown, Shield, AlertTriangle, CheckCircle, Info } from 'lucide-react'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

const MessageBubble = ({ message, showConfidence = true }) => {
  const [copied, setCopied] = useState(false)
  const [showDetails, setShowDetails] = useState(false)
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

  // Confidence display helpers
  const getConfidenceInfo = () => {
    const confidence = message.metadata?.confidence
    const level = message.metadata?.confidence_level
    
    if (confidence === undefined || confidence === null) {
      return null
    }
    
    const percentage = Math.round(confidence * 100)
    
    let color, bgColor, icon, label
    
    switch (level) {
      case 'HIGH':
        color = '#10b981'  // green
        bgColor = 'rgba(16, 185, 129, 0.1)'
        icon = <CheckCircle size={14} />
        label = 'High Confidence'
        break
      case 'MEDIUM':
        color = '#f59e0b'  // amber
        bgColor = 'rgba(245, 158, 11, 0.1)'
        icon = <Shield size={14} />
        label = 'Medium Confidence'
        break
      case 'LOW':
        color = '#ef4444'  // red
        bgColor = 'rgba(239, 68, 68, 0.1)'
        icon = <AlertTriangle size={14} />
        label = 'Low Confidence'
        break
      case 'VERY_LOW':
        color = '#dc2626'  // darker red
        bgColor = 'rgba(220, 38, 38, 0.1)'
        icon = <AlertTriangle size={14} />
        label = 'Very Low Confidence'
        break
      default:
        color = '#6b7280'  // gray
        bgColor = 'rgba(107, 114, 128, 0.1)'
        icon = <Info size={14} />
        label = 'Unknown'
    }
    
    return { percentage, color, bgColor, icon, label, level }
  }

  const confidenceInfo = !isUser ? getConfidenceInfo() : null

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
          <ReactMarkdown
            components={{
              // Style bold text with purple accent
              strong: ({node, ...props}) => (
                <strong style={{fontWeight: 600, color: '#8B5CF6'}} {...props} />
              ),
              // Style paragraphs with proper spacing
              p: ({node, ...props}) => (
                <p style={{marginBottom: '1em', lineHeight: '1.6', marginTop: 0}} {...props} />
              ),
              // Style horizontal rules (---) as separators
              hr: ({node, ...props}) => (
                <hr style={{
                  border: 'none',
                  borderTop: '1px solid rgba(139, 92, 246, 0.3)',
                  margin: '1.5em 0',
                  width: '100%'
                }} {...props} />
              ),
              // Style lists
              ul: ({node, ...props}) => (
                <ul style={{marginBottom: '1em', paddingLeft: '1.5em', lineHeight: '1.6'}} {...props} />
              ),
              ol: ({node, ...props}) => (
                <ol style={{marginBottom: '1em', paddingLeft: '1.5em', lineHeight: '1.6'}} {...props} />
              ),
              li: ({node, ...props}) => (
                <li style={{marginBottom: '0.5em'}} {...props} />
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Confidence Badge */}
        {showConfidence && confidenceInfo && (
          <div 
            className="confidence-badge"
            style={{ 
              backgroundColor: confidenceInfo.bgColor,
              color: confidenceInfo.color,
              borderColor: confidenceInfo.color
            }}
            onClick={() => setShowDetails(!showDetails)}
            title="Click for details"
          >
            <span className="confidence-icon">{confidenceInfo.icon}</span>
            <span className="confidence-text">{confidenceInfo.percentage}%</span>
            <span className="confidence-label">{confidenceInfo.label}</span>
          </div>
        )}

        {/* Confidence Details (expandable) */}
        {showDetails && confidenceInfo && (
          <div className="confidence-details" style={{ borderColor: confidenceInfo.color }}>
            <div className="confidence-detail-header">
              <span>Response Evaluation</span>
              <span 
                className="confidence-detail-method"
                style={{ color: confidenceInfo.color }}
              >
                {message.metadata?.evaluation_method === 'opik' ? '🔬 AI Evaluated' : '📊 Heuristic'}
              </span>
            </div>
            
            <div className="confidence-detail-row">
              <span>Overall Confidence</span>
              <div className="confidence-bar-container">
                <div 
                  className="confidence-bar"
                  style={{ 
                    width: `${confidenceInfo.percentage}%`,
                    backgroundColor: confidenceInfo.color 
                  }}
                />
              </div>
              <span style={{ color: confidenceInfo.color }}>{confidenceInfo.percentage}%</span>
            </div>
            
            {message.metadata?.sources_count !== undefined && (
              <div className="confidence-detail-row">
                <span>Sources Retrieved</span>
                <span>{message.metadata.sources_count}</span>
              </div>
            )}

            <p className="confidence-tip">
              {confidenceInfo.level === 'HIGH' && 
                "This response is well-supported by the retrieved documents."
              }
              {confidenceInfo.level === 'MEDIUM' && 
                "This response is reasonably supported. Consider reviewing sources for critical decisions."
              }
              {confidenceInfo.level === 'LOW' && 
                "This response may not be fully supported. Please verify against source documents."
              }
              {confidenceInfo.level === 'VERY_LOW' && 
                "This response should be independently verified before use."
              }
            </p>
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
