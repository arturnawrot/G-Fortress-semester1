import { useEffect } from "react";
import { useNavigate } from "react-router";

export default function Dashboard() {
  const navigate = useNavigate();

  useEffect(() => {
    // Check authentication status on component mount
    const isAuthenticated = localStorage.getItem("isAuthenticated");
    if (!isAuthenticated) {
    //   navigate("/login");
    }
  }, [navigate]);

  const handleLogout = () => {
    // Clear auth state
    localStorage.removeItem("isAuthenticated");
    // navigate("/login");
  };

  // Check if user is authenticated before rendering
  const isAuthenticated = localStorage.getItem("isAuthenticated");
  if (!isAuthenticated) {
    // return null; // or loading spinner
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
            </div>
            <div className="flex items-center">
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
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-medium text-gray-900 mb-2">
                Welcome to your dashboard!
              </h2>
              <p className="text-gray-500">
                This is a protected page that requires authentication.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}