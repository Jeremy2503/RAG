import { useState, useEffect } from 'react'
import { MessageSquare, Plus, Archive, Edit2, Check, X } from 'lucide-react'
import { chatAPI } from '../../services/api'

const ChatHistory = ({ onSelectSession, currentSessionId, refreshTrigger }) => {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState(null)
  const [editTitle, setEditTitle] = useState('')

  useEffect(() => {
    loadSessions()
  }, [refreshTrigger])

  const loadSessions = async () => {
    try {
      setLoading(true)
      const response = await chatAPI.getSessions()
      setSessions(response.sessions || [])
    } catch (error) {
      console.error('Error loading sessions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleNewChat = () => {
    onSelectSession(null)
  }

  const handleArchive = async (sessionId, e) => {
    e.stopPropagation()
    
    try {
      await chatAPI.archiveSession(sessionId)
      setSessions((prev) => prev.filter((s) => s.id !== sessionId))
    } catch (error) {
      console.error('Error archiving session:', error)
    }
  }

  const handleStartEdit = (session, e) => {
    e.stopPropagation()
    setEditingId(session.id)
    setEditTitle(session.title || 'New Conversation')
  }

  const handleCancelEdit = (e) => {
    e.stopPropagation()
    setEditingId(null)
    setEditTitle('')
  }

  const handleSaveEdit = async (sessionId, e) => {
    e.stopPropagation()
    
    try {
      await chatAPI.updateSessionTitle(sessionId, editTitle)
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title: editTitle } : s))
      )
      setEditingId(null)
      setEditTitle('')
    } catch (error) {
      console.error('Error updating session:', error)
    }
  }

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString)
      const now = new Date()
      const diffTime = Math.abs(now - date)
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays === 0) return 'Today'
      if (diffDays === 1) return 'Yesterday'
      if (diffDays < 7) return `${diffDays} days ago`
      
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      })
    } catch {
      return ''
    }
  }

  return (
    <div className="chat-history">
      <div className="chat-history-header">
        <h3>Conversations</h3>
        <button onClick={handleNewChat} className="btn btn-icon" title="New Chat">
          <Plus size={20} />
        </button>
      </div>

      <div className="chat-history-list">
        {loading ? (
          <div className="chat-history-loading">Loading...</div>
        ) : sessions.length === 0 ? (
          <div className="chat-history-empty">
            <MessageSquare size={32} />
            <p>No conversations yet</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className={`chat-history-item ${
                currentSessionId === session.id ? 'active' : ''
              }`}
              onClick={() => {
                if (editingId !== session.id) {
                  onSelectSession(session.id)
                }
              }}
            >
              <div className="chat-history-item-content">
                {editingId === session.id ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flex: 1 }}>
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      autoFocus
                      style={{
                        flex: 1,
                        padding: '4px 8px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '0.9rem'
                      }}
                    />
                    <button
                      onClick={(e) => handleSaveEdit(session.id, e)}
                      className="btn btn-icon-small"
                      title="Save"
                      style={{ color: '#10b981' }}
                    >
                      <Check size={16} />
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="btn btn-icon-small"
                      title="Cancel"
                      style={{ color: '#ef4444' }}
                    >
                      <X size={16} />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="chat-history-item-title">
                      {session.title || 'New Conversation'}
                    </div>
                    <div className="chat-history-item-date">
                      {formatDate(session.updated_at)}
                    </div>
                  </>
                )}
              </div>
              
              {editingId !== session.id && (
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button
                    onClick={(e) => handleStartEdit(session, e)}
                    className="btn btn-icon-small"
                    title="Rename"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    onClick={(e) => handleArchive(session.id, e)}
                    className="btn btn-icon-small"
                    title="Archive"
                  >
                    <Archive size={16} />
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default ChatHistory

