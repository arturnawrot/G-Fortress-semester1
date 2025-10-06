import { useEffect } from "react";
import { Link, useNavigate, NavLink, Outlet } from "react-router";
import { Bar } from "./dash/bar";
export default function UserDashboard() {
  const navigate = useNavigate();

  useEffect(() => {
    // Check authentication status on component mount
    //const isAuthenticated = localStorage.getItem("isAuthenticated");
    //if (!isAuthenticated) {
    //   navigate("/login");
    //}
  }, [navigate]);

  const handleLogout = () => {
    // Clear auth state
    //localStorage.removeItem("isAuthenticated");
    // navigate("/login");
  };

  // Check if user is authenticated before rendering
  //const isAuthenticated = localStorage.getItem("isAuthenticated");
  // if (!isAuthenticated) {
  // return null; // or loading spinner
  // }

  return (
    <div className="min-h-screen bg-purple-100">
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
          <nav>
            <div
              role="tablist"
              className="shadow tabs tabs-lift tabs-lg text-base-content"
            >
              <NavLink to="scanner" role="tab" className="tab ">
                Scanner
              </NavLink>
              <div className="tab-content border-gray-200  h-196 bg-gray-50 p-10">
                <Outlet />
                <div className="text-center"></div>
              </div>
              <NavLink to="scanhistory" role="tab" className="tab ">
                Scan History
              </NavLink>
              <div className="tab-content border-gray-200 h-196 bg-gray-50 p-10">
                <Outlet />
                <div className="text-center"></div>
              </div>
              <NavLink to="reports" role="tab" className="tab ">
                Reports
              </NavLink>
              <div className="tab-content border-gray-200 h-196 bg-gray-50 p-10">
                <Outlet />
                <div className="text-center"></div>
              </div>
              <NavLink to="help" role="tab" className="tab">
                Help
              </NavLink>
              <div className="tab-content  border-gray-200  h-196 bg-gray-50 p-10">
                <Outlet />
                <div className="text-center"></div>
              </div>
            </div>
          </nav>
        </div>
      </main>
    </div>
  );
}
