import { useState } from 'react'
import ChatInterface from '../components/Chat/ChatInterface'
import ChatHistory from '../components/Chat/ChatHistory'
import { LogOut, User, Settings, Sparkles } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

const UserDashboard = () => {
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleSelectSession = (sessionId) => {
    setCurrentSessionId(sessionId)
  }

  const handleSessionCreated = (sessionId) => {
    setCurrentSessionId(sessionId)
    setRefreshTrigger(prev => prev + 1)
  }

  const handleLogout = () => {
    logout()
    navigate('/login/user')
  }

  return (
    <div className="modern-dashboard">
      {/* Sidebar with Chat History */}
      <div className="modern-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <div className="brand-icon">
              <Sparkles size={24} />
            </div>
            <span className="brand-text">AI Assistant</span>
          </div>
        </div>

        <ChatHistory
          onSelectSession={handleSelectSession}
          currentSessionId={currentSessionId}
          refreshTrigger={refreshTrigger}
        />

        <div className="sidebar-footer">
          <div className="user-profile">
            <div className="profile-avatar">
              <User size={20} />
            </div>
            <div className="profile-info">
              <div className="profile-name">{user?.full_name || 'User'}</div>
              <div className="profile-email">{user?.email}</div>
            </div>
          </div>
          
          <div className="sidebar-actions">
            <button className="sidebar-action-btn" title="Settings">
              <Settings size={20} />
            </button>
            <button className="sidebar-action-btn" onClick={handleLogout} title="Logout">
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="modern-main">
        <ChatInterface
          sessionId={currentSessionId}
          onSessionCreated={handleSessionCreated}
        />
      </div>
    </div>
  )
}

export default UserDashboard
