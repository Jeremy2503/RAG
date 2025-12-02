import { useAuth } from '../context/AuthContext'
import { LogOut, ShieldCheck, User } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const Navbar = () => {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login/user')
  }

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h2>Multi-Agent RAG Platform</h2>
      </div>

      <div className="navbar-user">
        <div className="user-info">
          <div className="user-avatar">
            {isAdmin() ? <ShieldCheck size={20} /> : <User size={20} />}
          </div>
          <div className="user-details">
            <span className="user-name">{user?.full_name}</span>
            <span className="user-role">{user?.role}</span>
          </div>
        </div>

        <button onClick={handleLogout} className="btn btn-icon" title="Logout">
          <LogOut size={20} />
        </button>
      </div>
    </nav>
  )
}

export default Navbar

