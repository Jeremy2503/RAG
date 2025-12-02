import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Mail, Lock, User as UserIcon, Loader, Sparkles, MessageSquare } from 'lucide-react'

const UserRegister = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long')
      return
    }

    setLoading(true)

    const result = await register({
      email: formData.email,
      password: formData.password,
      full_name: formData.full_name,
      role: 'user'
    })

    if (result.success) {
      navigate('/login/user', { 
        state: { message: 'Registration successful! Please login.' }
      })
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
            <p className="brand-tagline">Start Your Journey</p>
            <p className="brand-description">
              Join thousands of users leveraging AI-powered document intelligence for smarter decisions
            </p>
            
            <div className="brand-features">
              <div className="feature-item">
                <Sparkles size={20} />
                <span>Instant AI Responses</span>
              </div>
              <div className="feature-item">
                <Sparkles size={20} />
                <span>Secure & Private</span>
              </div>
              <div className="feature-item">
                <Sparkles size={20} />
                <span>Always Learning</span>
              </div>
            </div>
          </div>
          
          <div className="brand-gradient-orb orb-1"></div>
          <div className="brand-gradient-orb orb-2"></div>
        </div>

        {/* Right Side - Register Form */}
        <div className="auth-form-side">
          <div className="auth-form-container">
            <div className="auth-header">
              <h2>Create an account</h2>
              <p>Get started with your intelligent assistant</p>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              {error && (
                <div className="auth-error">
                  <span>{error}</span>
                </div>
              )}

              <div className="form-group-modern">
                <label htmlFor="full_name">Full Name</label>
                <div className="input-with-icon">
                  <UserIcon size={20} className="input-icon" />
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    value={formData.full_name}
                    onChange={handleChange}
                    placeholder="Enter your full name"
                    required
                    disabled={loading}
                    className="modern-input"
                  />
                </div>
              </div>

              <div className="form-group-modern">
                <label htmlFor="email">Email</label>
                <div className="input-with-icon">
                  <Mail size={20} className="input-icon" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
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
                    name="password"
                    type="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Create a password"
                    required
                    minLength={8}
                    disabled={loading}
                    className="modern-input"
                  />
                </div>
                <small className="input-hint">Minimum 8 characters</small>
              </div>

              <div className="form-group-modern">
                <label htmlFor="confirmPassword">Confirm Password</label>
                <div className="input-with-icon">
                  <Lock size={20} className="input-icon" />
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    placeholder="Confirm your password"
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
                    <span>Creating account...</span>
                  </>
                ) : (
                  <span>Create Account</span>
                )}
              </button>
            </form>

            <div className="auth-divider">
              <span>OR</span>
            </div>

            <div className="auth-links">
              <p>
                Already have an account?{' '}
                <Link to="/login/user" className="auth-link">
                  Sign in
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserRegister
