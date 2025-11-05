import { Link, useLocation, useNavigate } from 'react-router';
import { useDispatch, useSelector } from 'react-redux';
import { logout, toggleAes, selectEnforceAes } from '../features/auth/authSlice';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const enforceAes = useSelector(selectEnforceAes);

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  const handleAesToggle = () => {
    dispatch(toggleAes());
  };

  const linkClasses = (path: string) =>
    `text-gray-600 hover:text-gray-900 ${location.pathname === path ? 'font-bold text-gray-900' : ''}`;

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-semibold text-gray-900">G-Fortress</h1>
              <div className="flex space-x-4">
                <Link to="/dashboard" className={linkClasses('/dashboard')}>
                  Dashboard
                </Link>
                <Link to="/reports" className={linkClasses('/reports')}>
                  Reports
                </Link>
                <Link to="/scheduled-scans" className={linkClasses('/scheduled-scans')}>
                  Scheduled Scans
                </Link>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <span className="mr-2 text-sm text-gray-700">AES Encryption</span>
                <button
                  onClick={handleAesToggle}
                  className={`relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none ${
                    enforceAes ? 'bg-indigo-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    aria-hidden="true"
                    className={`inline-block h-5 w-5 rounded-full bg-white shadow-lg transform ring-0 transition ease-in-out duration-200 ${
                      enforceAes ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
              <button
                onClick={handleLogout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">{children}</div>
      </main>
    </div>
  );
}