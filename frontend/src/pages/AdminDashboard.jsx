import { useState } from 'react'
import ChatInterface from '../components/Chat/ChatInterface'
import ChatHistory from '../components/Chat/ChatHistory'
import DocumentUpload from '../components/DocumentUpload'
import { MessageSquare, Upload as UploadIcon, LogOut, Settings, ShieldCheck, Sparkles } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('chat')
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

  const handleUploadComplete = (document) => {
    console.log('Document uploaded:', document)
  }

  const handleLogout = () => {
    logout()
    navigate('/login/admin')
  }

  return (
    <div className="modern-dashboard">
      {/* Sidebar */}
      <div className="modern-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <div className="brand-icon admin-brand">
              <ShieldCheck size={24} />
            </div>
            <span className="brand-text">Admin Portal</span>
          </div>
        </div>

        {/* Tab Navigation in Sidebar */}
        <div className="sidebar-tabs">
          <button
            className={`sidebar-tab ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageSquare size={20} />
            <span>Chat & Query</span>
          </button>
          <button
            className={`sidebar-tab ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            <UploadIcon size={20} />
            <span>Upload Documents</span>
          </button>
        </div>

        {/* Show Chat History only on Chat tab */}
        {activeTab === 'chat' && (
          <div className="sidebar-content">
            <ChatHistory
              onSelectSession={handleSelectSession}
              currentSessionId={currentSessionId}
              refreshTrigger={refreshTrigger}
            />
          </div>
        )}

        {/* User Profile Footer */}
        <div className="sidebar-footer">
          <div className="user-profile admin-profile">
            <div className="profile-avatar admin-avatar">
              <ShieldCheck size={20} />
            </div>
            <div className="profile-info">
              <div className="profile-name">{user?.full_name || 'Admin'}</div>
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

      {/* Main Content Area */}
      <div className="modern-main">
        {activeTab === 'chat' ? (
          <ChatInterface
            sessionId={currentSessionId}
            onSessionCreated={handleSessionCreated}
          />
        ) : (
          <DocumentUpload onUploadComplete={handleUploadComplete} />
        )}
      </div>
    </div>
  )
}

export default AdminDashboard
