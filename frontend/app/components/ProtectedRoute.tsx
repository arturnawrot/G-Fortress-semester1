import { useSelector } from 'react-redux';
import { Navigate, Outlet } from 'react-router'; // Changed from 'react-router-dom'
import { selectIsAuthenticated } from '../features/auth/authSlice';
import DashboardLayout from './DashboardLayout';

const ProtectedRoute = () => {
  const isAuthenticated = useSelector(selectIsAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <DashboardLayout>
      <Outlet />
    </DashboardLayout>
  );
};

export default ProtectedRoute;