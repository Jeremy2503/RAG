import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ShieldCheck, Mail, Lock, Loader, Sparkles, Settings } from 'lucide-react'

const AdminLogin = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const result = await login(email, password)

    if (result.success) {
      if (result.user.role === 'admin') {
        navigate('/admin/dashboard')
      } else {
        setError('Admin access required. Please use the user login.')
        setLoading(false)
      }
    } else {
      setError(result.error)
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-layout">
        {/* Left Side - Admin Brand */}
        <div className="auth-brand-side" style={{
          background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 50%, #6366f1 100%)'
        }}>
          <div className="brand-content">
            <div className="brand-logo">
              <ShieldCheck size={48} strokeWidth={1.5} />
            </div>
            <h1 className="brand-title">Admin Portal</h1>
            <p className="brand-tagline">System Management</p>
            <p className="brand-description">
              Secure administrative access to manage documents, users, and AI agent configurations
            </p>
            
            <div className="brand-features">
              <div className="feature-item">
                <Settings size={20} />
                <span>Complete System Control</span>
              </div>
              <div className="feature-item">
                <Sparkles size={20} />
                <span>User Management</span>
              </div>
              <div className="feature-item">
                <Sparkles size={20} />
                <span>Document Analytics</span>
              </div>
            </div>
          </div>
          
          <div className="brand-gradient-orb orb-1"></div>
          <div className="brand-gradient-orb orb-2"></div>
        </div>

        {/* Right Side - Admin Login Form */}
        <div className="auth-form-side">
          <div className="auth-form-container">
            <div className="auth-header">
              <h2>Admin Access</h2>
              <p>Sign in to the administration panel</p>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              {error && (
                <div className="auth-error">
                  <span>{error}</span>
                </div>
              )}

              <div className="form-group-modern">
                <label htmlFor="email">Admin Email</label>
                <div className="input-with-icon">
                  <Mail size={20} className="input-icon" />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="admin@example.com"
                    required
                    disabled={loading}
                    className="modern-input"
                  />
                </div>
              </div>

              <div className="form-group-modern">
                <label htmlFor="password">Password</label>
                <div className="input-with-icon">
                  <Lock size={20} className="input-icon" />
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter admin password"
                    required
                    disabled={loading}
                    className="modern-input"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="auth-submit-btn"
                style={{
                  background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)',
                  boxShadow: '0 4px 20px rgba(236, 72, 153, 0.4)'
                }}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader size={20} className="spinner" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <span>Sign In as Admin</span>
                )}
              </button>
            </form>

            <div className="auth-divider">
              <span>OR</span>
            </div>

            <div className="auth-links">
              <p>
                <Link to="/login/user" className="auth-link">
                  ← Back to User Login
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdminLogin
