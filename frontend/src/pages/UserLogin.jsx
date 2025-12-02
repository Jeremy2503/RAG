import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Mail, Lock, Loader, Sparkles, MessageSquare } from 'lucide-react'

const UserLogin = () => {
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
      if (result.user.role === 'user') {
        navigate('/user/dashboard')
      } else if (result.user.role === 'admin') {
        navigate('/admin/dashboard')
      } else {
        setError('Invalid user role')
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
        {/* Left Side - Brand */}
        <div className="auth-brand-side">
          <div className="brand-content">
            <div className="brand-logo">
              <MessageSquare size={48} strokeWidth={1.5} />
            </div>
            <h1 className="brand-title">Multi-Agent RAG</h1>
            <p className="brand-tagline">Intelligent Conversations</p>
            <p className="brand-description">
              Powered by advanced AI agents to provide accurate answers from your documents
            </p>
            
            <div className="brand-features">
              <div className="feature-item">
                <Sparkles size={20} />
                <span>Smart Document Analysis</span>
              </div>
              <div className="feature-item">
                <Sparkles size={20} />
                <span>Multi-Agent Intelligence</span>
              </div>
              <div className="feature-item">
                <Sparkles size={20} />
                <span>Real-time Responses</span>
              </div>
            </div>
          </div>
          
          <div className="brand-gradient-orb orb-1"></div>
          <div className="brand-gradient-orb orb-2"></div>
        </div>

        {/* Right Side - Login Form */}
        <div className="auth-form-side">
          <div className="auth-form-container">
            <div className="auth-header">
              <h2>Welcome back</h2>
              <p>Sign in to continue to your dashboard</p>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              {error && (
                <div className="auth-error">
                  <span>{error}</span>
                </div>
              )}

              <div className="form-group-modern">
                <label htmlFor="email">Email</label>
                <div className="input-with-icon">
                  <Mail size={20} className="input-icon" />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
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
                    placeholder="Enter your password"
                    required
                    disabled={loading}
                    className="modern-input"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="auth-submit-btn"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader size={20} className="spinner" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <span>Sign In</span>
                )}
              </button>
            </form>

            <div className="auth-divider">
              <span>OR</span>
            </div>

            <div className="auth-links">
              <p>
                Don't have an account?{' '}
                <Link to="/register" className="auth-link">
                  Create account
                </Link>
              </p>
              <p>
                <Link to="/login/admin" className="auth-link-secondary">
                  Admin Portal →
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserLogin
