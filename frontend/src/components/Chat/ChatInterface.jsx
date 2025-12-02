import { useState, useEffect, useRef } from 'react'
import { Send, Loader, Sparkles, RotateCcw } from 'lucide-react'
import { chatAPI } from '../../services/api'
import MessageBubble from './MessageBubble'

const ChatInterface = ({ sessionId: initialSessionId, onSessionCreated }) => {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(initialSessionId)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    setSessionId(initialSessionId)
    
    if (initialSessionId === null) {
      setMessages([])
      inputRef.current?.focus()
    }
  }, [initialSessionId])

  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId)
    } else if (sessionId === null) {
      setMessages([])
    }
  }, [sessionId])

  const loadSession = async (id) => {
    try {
      setLoading(true)
      const session = await chatAPI.getSession(id)
      setMessages(session.messages || [])
    } catch (error) {
      console.error('Error loading session:', error)
      setMessages([{
        role: 'assistant',
        content: 'Failed to load conversation. Please try again.',
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')

    const tempUserMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, tempUserMessage])

    setLoading(true)

    try {
      const response = await chatAPI.sendMessage(userMessage, sessionId)

      if (!sessionId && response.session_id) {
        setSessionId(response.session_id)
        if (onSessionCreated) {
          onSessionCreated(response.session_id)
        }
      }

      setMessages((prev) => [...prev, response.message])
    } catch (error) {
      console.error('Error sending message:', error)
      
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your request. Please try again.',
          timestamp: new Date().toISOString(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modern-chat-interface">
      {/* Chat Messages Area */}
      <div className="modern-chat-messages">
        {loading && messages.length === 0 ? (
          <div className="modern-empty-state">
            <div className="empty-state-icon loading">
              <Loader size={56} className="spinner" />
            </div>
            <h3>Loading conversation...</h3>
          </div>
        ) : messages.length === 0 ? (
          <div className="modern-empty-state">
            <div className="empty-state-icon">
              <Sparkles size={56} />
            </div>
            <h2>How can I help you today?</h2>
            <p>Ask me anything about HR policies, IT guidelines, or general information from your documents.</p>
            
            <div className="suggestion-chips">
              <button 
                className="suggestion-chip"
                onClick={() => setInput("What are the vacation policies?")}
              >
                <span>💼</span>
                Vacation Policies
              </button>
              <button 
                className="suggestion-chip"
                onClick={() => setInput("Tell me about IT security guidelines")}
              >
                <span>🔒</span>
                IT Security
              </button>
              <button 
                className="suggestion-chip"
                onClick={() => setInput("What are the work from home policies?")}
              >
                <span>🏠</span>
                Remote Work
              </button>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <MessageBubble key={index} message={message} />
            ))}
            
            {loading && messages.length > 0 && (
              <div className="typing-indicator">
                <div className="typing-avatar">
                  <Sparkles size={18} />
                </div>
                <div className="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="modern-chat-input-container">
        <form onSubmit={handleSubmit} className="modern-chat-input-form">
          <div className="input-wrapper">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={loading}
              className="modern-chat-input"
            />
            <button
              type="button"
              className="input-action-btn"
              title="Regenerate"
              disabled={messages.length === 0}
            >
              <RotateCcw size={20} />
            </button>
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="modern-send-btn"
              title="Send message"
            >
              <Send size={20} />
            </button>
          </div>
        </form>
        <p className="input-disclaimer">
          AI can make mistakes. Please verify important information.
        </p>
      </div>
    </div>
  )
}

export default ChatInterface
