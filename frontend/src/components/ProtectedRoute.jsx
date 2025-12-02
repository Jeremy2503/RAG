import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    )
  }

  if (!user) {
    // Not logged in, redirect to appropriate login page
    const loginPath = requiredRole === 'admin' ? '/login/admin' : '/login/user'
    return <Navigate to={loginPath} replace />
  }

  if (requiredRole && user.role !== requiredRole) {
    // Wrong role, redirect to appropriate login
    const loginPath = requiredRole === 'admin' ? '/login/admin' : '/login/user'
    return <Navigate to={loginPath} replace />
  }

  return children
}

export default ProtectedRoute

